from scapy.all import sniff, IP, TCP, UDP, ICMP
from collections import defaultdict
from datetime import datetime
import threading
import platform
import os
import time

# Global state
ip_count = defaultdict(int)
packet_buffer = []
buffer_lock = threading.Lock()
sniffer_thread = None
is_running = False
current_session_id = None


def get_blocked_ips_set(app):
    """Fetch currently active blocked IPs from database."""
    from models import BlockedIP
    with app.app_context():
        blocked = BlockedIP.query.filter_by(is_active=True).all()
        return {b.ip_address for b in blocked}


def block_ip_firewall(ip):
    """Block IP at OS firewall level."""
    try:
        os_type = platform.system()
        if os_type == "Linux":
            os.system(f"iptables -A INPUT -s {ip} -j DROP")
        elif os_type == "Windows":
            os.system(
                f'netsh advfirewall firewall add rule name="Block_{ip}" '
                f'dir=in action=block remoteip={ip}'
            )
    except Exception as e:
        print(f"Firewall block error for {ip}: {e}")


def unblock_ip_firewall(ip):
    """Remove IP block from OS firewall."""
    try:
        os_type = platform.system()
        if os_type == "Linux":
            os.system(f"iptables -D INPUT -s {ip} -j DROP")
        elif os_type == "Windows":
            os.system(
                f'netsh advfirewall firewall delete rule name="Block_{ip}"'
            )
    except Exception as e:
        print(f"Firewall unblock error for {ip}: {e}")


def process_packet(packet, app, socketio, threshold):
    """Process a captured packet — IDS detection + IPS blocking."""
    global current_session_id
    from models import db, Packet, Alert, BlockedIP

    try:
        if not packet.haslayer(IP):
            return

        src = packet[IP].src
        dst = packet[IP].dst
        protocol = "-"
        port = None
        packet_size = len(packet)
        status = "Normal"
        tag = ""

        # IDS: Count packets per source IP
        ip_count[src] += 1

        # Check if already blocked
        blocked_set = get_blocked_ips_set(app)

        if src in blocked_set:
            status = "BLOCKED"
            tag = "blocked"

        # IDS: Threshold detection
        elif ip_count[src] > threshold:
            status = "BLOCKED"
            tag = "blocked"

            # IPS: Block the IP
            with app.app_context():
                existing = BlockedIP.query.filter_by(ip_address=src, is_active=True).first()
                if not existing:
                    blocked = BlockedIP(
                        ip_address=src,
                        reason=f"High traffic detected ({ip_count[src]} packets) - Possible port scan",
                        is_active=True
                    )
                    db.session.add(blocked)
                    db.session.commit()
                    block_ip_firewall(src)

                    # Create alert
                    alert = Alert(
                        alert_type="Port Scan Detection",
                        description=f"High traffic from {src} ({ip_count[src]} packets exceeded threshold of {threshold})",
                        severity="high",
                        src_ip=src
                    )
                    db.session.add(alert)
                    db.session.commit()

                    # Notify frontend
                    socketio.emit('ip_blocked', {
                        'ip': src,
                        'reason': blocked.reason
                    })

        # Determine protocol
        if packet.haslayer(TCP):
            protocol = "TCP"
            port = packet[TCP].dport
            if tag != "blocked":
                tag = "tcp"
        elif packet.haslayer(UDP):
            protocol = "UDP"
            port = packet[UDP].dport
            if tag != "blocked":
                tag = "udp"
        elif packet.haslayer(ICMP):
            protocol = "ICMP"
            if tag != "blocked":
                tag = "icmp"

        timestamp = datetime.utcnow()

        # Buffer packet for batch insert
        packet_data = {
            'session_id': current_session_id,
            'src_ip': src,
            'dst_ip': dst,
            'protocol': protocol,
            'port': port,
            'packet_size': packet_size,
            'status': status,
            'timestamp': timestamp
        }

        with buffer_lock:
            packet_buffer.append(packet_data)

        # Emit to frontend in real-time
        socketio.emit('new_packet', {
            'time': timestamp.strftime("%H:%M:%S"),
            'src': src,
            'dst': dst,
            'protocol': protocol,
            'port': port if port else '-',
            'size': packet_size,
            'status': status,
            'tag': tag
        })

    except Exception as e:
        print(f"Packet processing error: {e}")


def batch_insert_packets(app):
    """Periodically flush buffered packets to the database."""
    from models import db, Packet, CaptureSession
    global packet_buffer

    while is_running:
        time.sleep(2)
        with buffer_lock:
            if not packet_buffer:
                continue
            to_insert = packet_buffer.copy()
            packet_buffer.clear()

        try:
            with app.app_context():
                for p in to_insert:
                    pkt = Packet(**p)
                    db.session.add(pkt)

                # Update session packet count
                if current_session_id:
                    session = CaptureSession.query.get(current_session_id)
                    if session:
                        session.packet_count += len(to_insert)

                db.session.commit()
        except Exception as e:
            print(f"Batch insert error: {e}")


def start_sniffing(app, socketio, session_id, threshold=20):
    """Start packet capture in a background thread."""
    global is_running, sniffer_thread, current_session_id, ip_count

    if is_running:
        return False

    is_running = True
    current_session_id = session_id
    ip_count.clear()

    def sniff_target():
        sniff(
            prn=lambda pkt: process_packet(pkt, app, socketio, threshold),
            store=False,
            stop_filter=lambda x: not is_running
        )

    sniffer_thread = threading.Thread(target=sniff_target, daemon=True)
    sniffer_thread.start()

    # Start batch inserter
    batch_thread = threading.Thread(target=batch_insert_packets, args=(app,), daemon=True)
    batch_thread.start()

    return True


def stop_sniffing(app):
    """Stop packet capture and flush remaining buffer."""
    global is_running, current_session_id
    from models import db, CaptureSession

    is_running = False

    # Flush remaining buffer
    with buffer_lock:
        remaining = packet_buffer.copy()
        packet_buffer.clear()

    if remaining:
        try:
            from models import Packet
            with app.app_context():
                for p in remaining:
                    pkt = Packet(**p)
                    db.session.add(pkt)

                if current_session_id:
                    session = CaptureSession.query.get(current_session_id)
                    if session:
                        session.packet_count += len(remaining)
                        session.status = 'stopped'
                        session.end_time = datetime.utcnow()

                db.session.commit()
        except Exception as e:
            print(f"Final flush error: {e}")
    else:
        try:
            with app.app_context():
                if current_session_id:
                    session = CaptureSession.query.get(current_session_id)
                    if session:
                        session.status = 'stopped'
                        session.end_time = datetime.utcnow()
                        db.session.commit()
        except Exception as e:
            print(f"Session close error: {e}")

    current_session_id = None
    return True

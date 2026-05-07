from flask import Blueprint, render_template, request, Response, flash
from flask_login import login_required
from models import db, Packet, CaptureSession, User
from sqlalchemy import and_
from datetime import datetime
import csv
import io

packets_bp = Blueprint('packets', __name__)


@packets_bp.route('/packets')
@login_required
def packet_list():
    """Paginated packet history with filters/search."""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Filter parameters
    src_ip = request.args.get('src_ip', '').strip()
    dst_ip = request.args.get('dst_ip', '').strip()
    protocol = request.args.get('protocol', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    # Build query with JOIN: Packets + CaptureSession + User
    query = db.session.query(
        Packet, CaptureSession.session_name, User.username
    ).join(
        CaptureSession, Packet.session_id == CaptureSession.id
    ).join(
        User, CaptureSession.user_id == User.id
    )

    # Apply filters
    if src_ip:
        query = query.filter(Packet.src_ip.like(f'%{src_ip}%'))
    if dst_ip:
        query = query.filter(Packet.dst_ip.like(f'%{dst_ip}%'))
    if protocol:
        query = query.filter(Packet.protocol == protocol)
    if status:
        query = query.filter(Packet.status == status)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Packet.timestamp >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Packet.timestamp <= dt_to)
        except ValueError:
            pass

    # Order and paginate
    query = query.order_by(Packet.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('packets.html',
                           packets=pagination.items,
                           pagination=pagination,
                           filters={
                               'src_ip': src_ip,
                               'dst_ip': dst_ip,
                               'protocol': protocol,
                               'status': status,
                               'date_from': date_from,
                               'date_to': date_to
                           })


@packets_bp.route('/packets/export')
@login_required
def export_csv():
    """Export filtered packets to CSV."""
    src_ip = request.args.get('src_ip', '').strip()
    dst_ip = request.args.get('dst_ip', '').strip()
    protocol = request.args.get('protocol', '').strip()
    status = request.args.get('status', '').strip()

    query = db.session.query(
        Packet, CaptureSession.session_name, User.username
    ).join(
        CaptureSession, Packet.session_id == CaptureSession.id
    ).join(
        User, CaptureSession.user_id == User.id
    )

    if src_ip:
        query = query.filter(Packet.src_ip.like(f'%{src_ip}%'))
    if dst_ip:
        query = query.filter(Packet.dst_ip.like(f'%{dst_ip}%'))
    if protocol:
        query = query.filter(Packet.protocol == protocol)
    if status:
        query = query.filter(Packet.status == status)

    packets = query.order_by(Packet.timestamp.desc()).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Time', 'Source IP', 'Destination IP', 'Protocol',
                     'Port', 'Size', 'Status', 'Session', 'Captured By'])

    for pkt, session_name, username in packets:
        writer.writerow([
            pkt.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            pkt.src_ip, pkt.dst_ip, pkt.protocol,
            pkt.port or '-', pkt.packet_size or '-',
            pkt.status, session_name, username
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=packets_export.csv'}
    )

/**
 * NetGuard — Dashboard Real-Time (Socket.IO)
 */

let socket = null;
let packetCount = 0;
const MAX_TABLE_ROWS = 200;

function connectSocket() {
    socket = io();

    socket.on('connect', function () {
        console.log('Socket.IO connected');
    });

    socket.on('new_packet', function (data) {
        addPacketRow(data);
        packetCount++;
        updatePacketCounter();
    });

    socket.on('ip_blocked', function (data) {
        showBlockNotification(data.ip, data.reason);
        refreshStats();
    });

    socket.on('disconnect', function () {
        console.log('Socket.IO disconnected');
    });
}

function addPacketRow(pkt) {
    const tbody = document.getElementById('packetTableBody');
    if (!tbody) return;

    const row = document.createElement('tr');
    row.className = 'packet-row-new ';

    if (pkt.tag === 'blocked') row.className += 'row-blocked';
    else if (pkt.tag === 'tcp') row.className += 'row-tcp';
    else if (pkt.tag === 'udp') row.className += 'row-udp';
    else if (pkt.tag === 'icmp') row.className += 'row-icmp';

    const protocolClass = 'protocol-' + (pkt.protocol || '-').toLowerCase();
    const statusBadge = pkt.status === 'BLOCKED'
        ? '<span class="badge bg-danger"><i class="bi bi-ban"></i> BLOCKED</span>'
        : '<span class="badge bg-success">Normal</span>';

    row.innerHTML =
        '<td>' + pkt.time + '</td>' +
        '<td><code>' + pkt.src + '</code></td>' +
        '<td><code>' + pkt.dst + '</code></td>' +
        '<td><span class="protocol-badge ' + protocolClass + '">' + pkt.protocol + '</span></td>' +
        '<td>' + pkt.port + '</td>' +
        '<td>' + pkt.size + '</td>' +
        '<td>' + statusBadge + '</td>';

    tbody.insertBefore(row, tbody.firstChild);

    // Limit table rows
    while (tbody.children.length > MAX_TABLE_ROWS) {
        tbody.removeChild(tbody.lastChild);
    }
}

function updatePacketCounter() {
    const el = document.getElementById('packetCounter');
    if (el) {
        el.textContent = formatNumber(packetCount) + ' packets';
    }
}

function startCapture() {
    fetch('/api/capture/start', { method: 'POST' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                document.getElementById('btnStartCapture').disabled = true;
                document.getElementById('btnStopCapture').disabled = false;
                document.getElementById('captureStatus').textContent = 'Running';
                document.getElementById('captureStatus').className = 'capture-status badge bg-success';
                document.getElementById('liveIndicator').style.display = 'inline-flex';
            } else {
                alert(data.message || 'Failed to start capture');
            }
        })
        .catch(function (err) {
            alert('Error: ' + err.message);
        });
}

function stopCapture() {
    fetch('/api/capture/stop', { method: 'POST' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.success) {
                document.getElementById('btnStartCapture').disabled = false;
                document.getElementById('btnStopCapture').disabled = true;
                document.getElementById('captureStatus').textContent = 'Stopped';
                document.getElementById('captureStatus').className = 'capture-status badge bg-secondary';
                document.getElementById('liveIndicator').style.display = 'none';
                refreshStats();
            }
        })
        .catch(function (err) {
            alert('Error: ' + err.message);
        });
}

function clearTable() {
    const tbody = document.getElementById('packetTableBody');
    if (tbody) tbody.innerHTML = '';
    packetCount = 0;
    updatePacketCounter();
}

function refreshStats() {
    fetch('/api/stats')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var el;
            el = document.getElementById('statTotalPackets');
            if (el) el.textContent = formatNumber(data.total_packets);

            el = document.getElementById('statActiveSessions');
            if (el) el.textContent = data.active_sessions;

            el = document.getElementById('statBlockedIPs');
            if (el) el.textContent = data.blocked_count;

            el = document.getElementById('statAlerts');
            if (el) el.textContent = data.alert_count;

            if (data.protocol_stats) {
                updateProtocolChart(data.protocol_stats);
            }
        });
}

function showBlockNotification(ip, reason) {
    const container = document.querySelector('.content-wrapper');
    if (!container) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show glass-alert';
    alertDiv.innerHTML =
        '<i class="bi bi-shield-exclamation"></i> <strong>IP Blocked:</strong> ' +
        ip + ' — ' + reason +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(function () {
        var bsAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        if (bsAlert) bsAlert.close();
    }, 8000);
}

// Auto-refresh stats every 10 seconds
setInterval(refreshStats, 10000);

// Connect socket on page load
document.addEventListener('DOMContentLoaded', function () {
    connectSocket();

    // Count existing rows
    var tbody = document.getElementById('packetTableBody');
    if (tbody) {
        packetCount = tbody.children.length;
        updatePacketCounter();
    }
});

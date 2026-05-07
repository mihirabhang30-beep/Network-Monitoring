from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Packet, CaptureSession, Alert, BlockedIP
from sqlalchemy import func
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with stats and real-time monitoring."""
    # Stats
    total_packets = Packet.query.count()
    active_sessions = CaptureSession.query.filter_by(status='running').count()
    blocked_count = BlockedIP.query.filter_by(is_active=True).count()
    alert_count = Alert.query.filter_by(resolved=False).count()

    # Recent packets (last 50)
    recent_packets = Packet.query.order_by(Packet.timestamp.desc()).limit(50).all()

    # Protocol distribution — convert Row objects to plain lists for JSON
    protocol_rows = db.session.query(
        Packet.protocol,
        func.count(Packet.id)
    ).group_by(Packet.protocol).all()
    protocol_stats = [[row[0], row[1]] for row in protocol_rows]

    # Top source IPs — convert Row objects to plain lists for JSON
    source_rows = db.session.query(
        Packet.src_ip,
        func.count(Packet.id).label('count')
    ).group_by(Packet.src_ip).order_by(func.count(Packet.id).desc()).limit(10).all()
    top_sources = [[row[0], row[1]] for row in source_rows]

    return render_template('dashboard.html',
                           total_packets=total_packets,
                           active_sessions=active_sessions,
                           blocked_count=blocked_count,
                           alert_count=alert_count,
                           recent_packets=recent_packets,
                           protocol_stats=protocol_stats,
                           top_sources=top_sources)


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for live stats updates."""
    total_packets = Packet.query.count()
    active_sessions = CaptureSession.query.filter_by(status='running').count()
    blocked_count = BlockedIP.query.filter_by(is_active=True).count()
    alert_count = Alert.query.filter_by(resolved=False).count()

    protocol_stats = db.session.query(
        Packet.protocol,
        func.count(Packet.id)
    ).group_by(Packet.protocol).all()

    return jsonify({
        'total_packets': total_packets,
        'active_sessions': active_sessions,
        'blocked_count': blocked_count,
        'alert_count': alert_count,
        'protocol_stats': {p: c for p, c in protocol_stats}
    })

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Alert, Packet, AuditLog
from datetime import datetime

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/alerts')
@login_required
def alert_list():
    """View all IDS alerts with filters."""
    page = request.args.get('page', 1, type=int)
    severity = request.args.get('severity', '').strip()
    resolved_filter = request.args.get('resolved', '').strip()

    # JOIN: Alerts + Packets
    query = db.session.query(Alert).outerjoin(Packet, Alert.packet_id == Packet.id)

    if severity:
        query = query.filter(Alert.severity == severity)
    if resolved_filter == 'yes':
        query = query.filter(Alert.resolved == True)
    elif resolved_filter == 'no':
        query = query.filter(Alert.resolved == False)

    query = query.order_by(Alert.created_at.desc())
    pagination = query.paginate(page=page, per_page=25, error_out=False)

    # Stats
    total_alerts = Alert.query.count()
    unresolved = Alert.query.filter_by(resolved=False).count()
    critical = Alert.query.filter_by(severity='critical', resolved=False).count()

    return render_template('alerts.html',
                           alerts=pagination.items,
                           pagination=pagination,
                           total_alerts=total_alerts,
                           unresolved=unresolved,
                           critical=critical,
                           filters={'severity': severity, 'resolved': resolved_filter})


@alerts_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Mark an alert as resolved (UPDATE operation)."""
    alert = Alert.query.get_or_404(alert_id)
    alert.resolved = True

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action='RESOLVE_ALERT',
        details=f'Resolved alert #{alert_id}: {alert.alert_type} from {alert.src_ip}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Alert #{alert_id} resolved.', 'success')
    return redirect(url_for('alerts.alert_list'))


@alerts_bp.route('/alerts/<int:alert_id>/delete', methods=['POST'])
@login_required
def delete_alert(alert_id):
    """Delete an alert (DELETE operation). Admin only."""
    if current_user.role != 'admin':
        flash('Permission denied.', 'danger')
        return redirect(url_for('alerts.alert_list'))

    alert = Alert.query.get_or_404(alert_id)

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action='DELETE_ALERT',
        details=f'Deleted alert #{alert_id}: {alert.alert_type} from {alert.src_ip}',
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(alert)
    db.session.commit()

    flash(f'Alert #{alert_id} deleted.', 'success')
    return redirect(url_for('alerts.alert_list'))

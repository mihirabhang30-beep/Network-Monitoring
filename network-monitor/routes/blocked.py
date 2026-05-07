from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, BlockedIP, AuditLog, User
from sniffer import unblock_ip_firewall, block_ip_firewall
from datetime import datetime

blocked_bp = Blueprint('blocked', __name__)


@blocked_bp.route('/blocked')
@login_required
def blocked_list():
    """View blocked IPs with JOIN to show who blocked them."""
    page = request.args.get('page', 1, type=int)

    # JOIN: BlockedIP + User (who blocked)
    query = db.session.query(
        BlockedIP, User.username
    ).outerjoin(
        User, BlockedIP.blocked_by == User.id
    ).order_by(BlockedIP.blocked_at.desc())

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    active_count = BlockedIP.query.filter_by(is_active=True).count()
    total_count = BlockedIP.query.count()

    return render_template('blocked_ips.html',
                           blocked_items=pagination.items,
                           pagination=pagination,
                           active_count=active_count,
                           total_count=total_count)


@blocked_bp.route('/blocked/add', methods=['POST'])
@login_required
def block_ip():
    """Manually block an IP (admin only)."""
    if current_user.role != 'admin':
        flash('Permission denied. Admin only.', 'danger')
        return redirect(url_for('blocked.blocked_list'))

    ip = request.form.get('ip_address', '').strip()
    reason = request.form.get('reason', 'Manually blocked by admin').strip()

    if not ip:
        flash('Please enter an IP address.', 'danger')
        return redirect(url_for('blocked.blocked_list'))

    # Check if already blocked
    existing = BlockedIP.query.filter_by(ip_address=ip, is_active=True).first()
    if existing:
        flash(f'{ip} is already blocked.', 'warning')
        return redirect(url_for('blocked.blocked_list'))

    blocked = BlockedIP(
        ip_address=ip,
        reason=reason,
        blocked_by=current_user.id,
        is_active=True
    )
    db.session.add(blocked)

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action='BLOCK_IP',
        details=f'Manually blocked IP {ip}: {reason}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    # Block at firewall level
    block_ip_firewall(ip)

    flash(f'{ip} has been blocked.', 'success')
    return redirect(url_for('blocked.blocked_list'))


@blocked_bp.route('/blocked/<int:blocked_id>/unblock', methods=['POST'])
@login_required
def unblock_ip_route(blocked_id):
    """Unblock an IP (UPDATE operation)."""
    if current_user.role != 'admin':
        flash('Permission denied. Admin only.', 'danger')
        return redirect(url_for('blocked.blocked_list'))

    blocked = BlockedIP.query.get_or_404(blocked_id)

    if not blocked.is_active:
        flash('This IP is already unblocked.', 'info')
        return redirect(url_for('blocked.blocked_list'))

    # UPDATE operation
    blocked.is_active = False
    blocked.unblocked_at = datetime.utcnow()

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action='UNBLOCK_IP',
        details=f'Unblocked IP {blocked.ip_address}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    # Remove from firewall
    unblock_ip_firewall(blocked.ip_address)

    flash(f'{blocked.ip_address} has been unblocked.', 'success')
    return redirect(url_for('blocked.blocked_list'))

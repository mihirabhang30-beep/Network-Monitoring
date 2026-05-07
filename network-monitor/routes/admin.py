from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, AuditLog, CaptureSession
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    """List all users (admin only)."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account (DELETE operation)."""
    if user_id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.user_list'))

    user = User.query.get_or_404(user_id)

    # Audit log before deletion
    log = AuditLog(
        user_id=current_user.id,
        action='DELETE_USER',
        details=f'Deleted user {user.username} (ID: {user.id})',
        ip_address=request.remote_addr
    )
    db.session.add(log)

    # Delete related sessions
    CaptureSession.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def toggle_role(user_id):
    """Toggle user role between admin and viewer."""
    if user_id == current_user.id:
        flash('Cannot change your own role.', 'danger')
        return redirect(url_for('admin.user_list'))

    user = User.query.get_or_404(user_id)
    old_role = user.role
    user.role = 'admin' if user.role == 'viewer' else 'viewer'

    log = AuditLog(
        user_id=current_user.id,
        action='CHANGE_ROLE',
        details=f'Changed {user.username} role from {old_role} to {user.role}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'{user.username} role changed to {user.role}.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs with filters."""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('user_id', '', type=str).strip()

    # JOIN: AuditLog + User
    query = db.session.query(
        AuditLog, User.username
    ).join(
        User, AuditLog.user_id == User.id
    )

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if user_filter:
        try:
            query = query.filter(AuditLog.user_id == int(user_filter))
        except ValueError:
            pass

    query = query.order_by(AuditLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=30, error_out=False)

    # Get unique actions for filter dropdown
    actions = db.session.query(AuditLog.action).distinct().all()
    users = User.query.all()

    return render_template('admin/audit_logs.html',
                           logs=pagination.items,
                           pagination=pagination,
                           actions=[a[0] for a in actions],
                           users=users,
                           filters={'action': action_filter, 'user_id': user_filter})


@admin_bp.route('/sessions')
@login_required
@admin_required
def session_list():
    """View all capture sessions."""
    page = request.args.get('page', 1, type=int)

    query = db.session.query(
        CaptureSession, User.username
    ).join(
        User, CaptureSession.user_id == User.id
    ).order_by(CaptureSession.start_time.desc())

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    return render_template('admin/sessions.html',
                           sessions=pagination.items,
                           pagination=pagination)


@admin_bp.route('/sessions/<int:session_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_session(session_id):
    """Delete a capture session and its packets (DELETE operation)."""
    session = CaptureSession.query.get_or_404(session_id)

    log = AuditLog(
        user_id=current_user.id,
        action='DELETE_SESSION',
        details=f'Deleted session "{session.session_name}" (ID: {session_id}, {session.packet_count} packets)',
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(session)  # Cascades to packets
    db.session.commit()

    flash(f'Session "{session.session_name}" deleted.', 'success')
    return redirect(url_for('admin.session_list'))

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User accounts for authentication and role-based access."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='viewer')  # 'admin' or 'viewer'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    sessions = db.relationship('CaptureSession', backref='user', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    blocked_ips = db.relationship('BlockedIP', backref='blocked_by_user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class CaptureSession(db.Model):
    """Packet capture sessions started by users."""
    __tablename__ = 'capture_sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_name = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='running')  # running/stopped/completed
    packet_count = db.Column(db.Integer, default=0)

    # Relationships
    packets = db.relationship('Packet', backref='session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CaptureSession {self.session_name}>'


class Packet(db.Model):
    """Captured network packets."""
    __tablename__ = 'packets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('capture_sessions.id'), nullable=False)
    src_ip = db.Column(db.String(45), nullable=False)
    dst_ip = db.Column(db.String(45), nullable=False)
    protocol = db.Column(db.String(10), nullable=False)
    port = db.Column(db.Integer, nullable=True)
    packet_size = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Normal')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    alerts = db.relationship('Alert', backref='packet', lazy=True)

    # Index for faster queries
    __table_args__ = (
        db.Index('idx_src_ip', 'src_ip'),
        db.Index('idx_dst_ip', 'dst_ip'),
        db.Index('idx_protocol', 'protocol'),
        db.Index('idx_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f'<Packet {self.src_ip} -> {self.dst_ip}>'


class Alert(db.Model):
    """IDS alerts triggered by suspicious activity."""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    packet_id = db.Column(db.Integer, db.ForeignKey('packets.id'), nullable=True)
    alert_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(10), nullable=False, default='medium')  # low/medium/high/critical
    src_ip = db.Column(db.String(45), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Alert {self.alert_type} - {self.src_ip}>'


class BlockedIP(db.Model):
    """IPs blocked by the IPS system."""
    __tablename__ = 'blocked_ips'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    reason = db.Column(db.String(300), nullable=False)
    blocked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    blocked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    unblocked_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<BlockedIP {self.ip_address}>'


class AuditLog(db.Model):
    """Audit trail of user actions for security monitoring."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'

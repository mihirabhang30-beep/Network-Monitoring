"""
NetGuard — Network Monitoring Tool (IDS + IPS)
Main Flask Application Entry Point
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_login import LoginManager, login_required, current_user
from config import Config
from models import db, User, CaptureSession
from datetime import datetime

# Initialize extensions
socketio = SocketIO()
login_manager = LoginManager()


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.packets import packets_bp
    from routes.alerts import alerts_bp
    from routes.blocked import blocked_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(packets_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(blocked_bp)
    app.register_blueprint(admin_bp)

    # --- Capture API Routes ---
    @app.route('/api/capture/start', methods=['POST'])
    @login_required
    def api_start_capture():
        """Start packet capture."""
        from sniffer import start_sniffing

        # Create a new capture session
        session = CaptureSession(
            user_id=current_user.id,
            session_name=f"Capture_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            status='running'
        )
        db.session.add(session)
        db.session.commit()

        success = start_sniffing(
            app=app,
            socketio=socketio,
            session_id=session.id,
            threshold=app.config.get('IDS_THRESHOLD', 20)
        )

        if success:
            return jsonify({'success': True, 'session_id': session.id})
        else:
            session.status = 'stopped'
            db.session.commit()
            return jsonify({'success': False, 'message': 'Capture already running'})

    @app.route('/api/capture/stop', methods=['POST'])
    @login_required
    def api_stop_capture():
        """Stop packet capture."""
        from sniffer import stop_sniffing
        stop_sniffing(app)
        return jsonify({'success': True})

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Page not found'}), 404

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Access forbidden'}), 403

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


# Create the app
app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 55)
    print("  NetGuard — Network Monitoring Tool (IDS + IPS)")
    print("  Open: http://localhost:5000")
    print("  NOTE: Run as Administrator for packet capture!")
    print("=" * 55 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

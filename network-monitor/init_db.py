"""
NetGuard — Database Initialization Script
Creates all tables and seeds an admin user.

Usage:
    python init_db.py

Make sure MySQL server is running and the database exists:
    CREATE DATABASE network_monitor;
"""

from app import app
from models import db, User
from werkzeug.security import generate_password_hash
import sys


def init_database():
    """Create all tables and seed initial data."""
    with app.app_context():
        print("[*] Creating all database tables...")
        db.create_all()
        print("[+] Tables created successfully!")

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("[*] Creating default admin user...")
            admin = User(
                username='admin',
                email='admin@netguard.local',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("[+] Admin user created:")
            print("    Username: admin")
            print("    Password: admin123")
            print("    (Change this password after first login!)")
        else:
            print("[i] Admin user already exists, skipping.")

        print("\n[+] Database initialization complete!")
        print("[*] You can now run: python app.py")


if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n[!] ERROR: {e}")
        print("\nMake sure:")
        print("  1. MySQL server is running")
        print("  2. Database 'network_monitor' exists:")
        print("     CREATE DATABASE network_monitor;")
        print("  3. config.py has correct DB credentials")
        sys.exit(1)

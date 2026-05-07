import os

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'netmon-secret-key-change-in-production'

    # --- SQLite (works immediately, no setup needed) ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'network_monitor.db')

    # --- MySQL (uncomment below & comment SQLite above for production) ---
    # DB_USER = os.environ.get('DB_USER', 'root')
    # DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    # DB_HOST = os.environ.get('DB_HOST', 'localhost')
    # DB_PORT = os.environ.get('DB_PORT', '3306')
    # DB_NAME = os.environ.get('DB_NAME', 'network_monitor')
    # SQLALCHEMY_DATABASE_URI = (
    #     f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IDS Configuration
    IDS_THRESHOLD = int(os.environ.get('IDS_THRESHOLD', '20'))

    # Packet batch insert interval (seconds)
    BATCH_INSERT_INTERVAL = 2

    # Pagination
    PACKETS_PER_PAGE = 50
    ALERTS_PER_PAGE = 25
    LOGS_PER_PAGE = 30

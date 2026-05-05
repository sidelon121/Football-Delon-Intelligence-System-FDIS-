"""
FDIS Configuration
Football Data Intelligence System
"""
from dotenv import load_dotenv
import os

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'fdis-secret-key-change-in-production'

    # 🔥 PAKSA LANGSUNG KE DATABASE YANG BENAR
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/data_statistik"

    SQLALCHEMY_TRACK_MODIFICATIONS = False # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    # API-Football Configuration
    API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '')
    API_FOOTBALL_BASE_URL = 'https://fbref.com/en/matches/d90d2b6c/Manchester-United-Brentford-April-27-2026-Premier-League'
    API_FOOTBALL_DAILY_LIMIT = 100
    API_FOOTBALL_RATE_LIMIT = 10  # requests per minute

    # Report settings
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'reports')

    # Allowed upload extensions
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

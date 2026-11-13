import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'labstock-ai-dev-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'labstock.db')
    SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    DEBUG = True

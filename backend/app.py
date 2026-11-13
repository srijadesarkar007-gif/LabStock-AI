import os
import sys

# Ensure project root is in Python's search path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from backend.config import Config
from backend.routes.views import views_bp
from backend.routes.api import api_bp
from backend.routes.schedules import schedules_bp
from backend.routes.alerts import alerts_bp
from backend.db import init_db


def create_app(config_class=Config):
    """Application factory for LabStock AI."""
    app = Flask(
        __name__,
        template_folder=config_class.TEMPLATE_DIR,
        static_folder=config_class.STATIC_DIR
    )
    app.config.from_object(config_class)

    # Initialize SQLite database and seed starter data if needed
    init_db()

    # Register blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(schedules_bp, url_prefix='/schedules')
    app.register_blueprint(alerts_bp, url_prefix='/alerts')

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 65)
    print("  LabStock AI – Engineering Laboratory Inventory & AI System  ")
    print("  Dashboard URL: http://127.0.0.1:5000                        ")
    print("  Practical Schedules: http://127.0.0.1:5000/schedules       ")
    print("  Inventory Alerts: http://127.0.0.1:5000/alerts             ")
    print("  Admin Portal: http://127.0.0.1:5000/login                   ")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)

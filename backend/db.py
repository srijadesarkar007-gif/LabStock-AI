import sqlite3
import os
from backend.config import Config


def get_db():
    """Returns a SQLite connection with row access by column name."""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ensure database exists and tables are initialized."""
    if not os.path.exists(Config.DATABASE_PATH):
        from database.init_db import init_database
        init_database(Config.DATABASE_PATH, Config.SCHEMA_PATH)

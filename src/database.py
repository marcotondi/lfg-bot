# src/database.py

"""
Hanldes SQLite database connection and initialization.
"""

import sqlite3
import os
from src.config import DB_FILE

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def validate_db():
    """Checks if the database schema is valid (all required tables exist)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    required_tables = {"users", "tables", "registrations"}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    conn.close()
    missing = required_tables - tables
    return len(missing) == 0, missing

def bootstrap_db_from_migration():
    """Initializza il database usando lo script di migrazione principale."""
    migration_path = os.path.join(os.path.dirname(__file__), "..", "db", "migrations", "20250926122852_initial_schema.sql")
    conn = get_db_connection()
    with open(migration_path, "r") as f:
        conn.executescript(f.read())
    conn.close()

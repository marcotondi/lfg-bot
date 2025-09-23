# src/database.py

"""
Hanldes SQLite database connection and initialization.
"""

import sqlite3
from src.config import DB_FILE

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the required schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        mute BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Add is_master and is_admin columns if they don't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if "is_master" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_master BOOLEAN DEFAULT 0")
    if "is_admin" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")

    # Create tables table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        master_id INTEGER NOT NULL,
        type TEXT CHECK(type IN ('one_shot', 'campaign')) NOT NULL,
        game TEXT NOT NULL,
        name TEXT NOT NULL,
        max_players INTEGER NOT NULL,
        description TEXT,
        image TEXT,
        num_sessions INTEGER,
        active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (master_id) REFERENCES users(id)
    );
    """)

    # Create registrations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (table_id) REFERENCES tables(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(table_id, user_id)
    );
    """)

    # Create trigger for registrations updated_at
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_registrations_updated_at
    AFTER UPDATE ON registrations
    FOR EACH ROW
    BEGIN
        UPDATE registrations SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END;
    """)

    conn.commit()
    conn.close()

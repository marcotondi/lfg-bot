# src/database.py
"""
Handles SQLite database connection and initialization.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Set, Tuple
from src.config import DB_FILE

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper cleanup even if errors occur.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys (disabled by default in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def validate_db() -> Tuple[bool, Set[str]]:
    """
    Checks if the database schema is valid (all required tables exist).
    
    Returns:
        Tuple of (is_valid, missing_tables)
    """
    required_tables = {"users", "tables", "registrations"}
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = {row["name"] for row in cursor.fetchall()}
            missing = required_tables - tables
            
            is_valid = len(missing) == 0
            if not is_valid:
                logger.warning(f"Missing tables in database: {missing}")
            
            return is_valid, missing
    except sqlite3.Error as e:
        logger.error(f"Failed to validate database: {e}")
        return False, required_tables


def bootstrap_db_from_migration() -> None:
    """
    Initializes the database using the main migration script.
    
    Raises:
        FileNotFoundError: If migration file doesn't exist
        sqlite3.Error: If migration fails
    """
    migration_path = os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "db", 
        "migrations", 
        "20250926122852_initial_schema.sql"
    )
    
    if not os.path.exists(migration_path):
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    try:
        with get_db_connection() as conn:
            with open(migration_path, "r", encoding="utf-8") as f:
                migration_sql = f.read()
            conn.executescript(migration_sql)
            logger.info("Database bootstrapped successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to bootstrap database: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to read migration file: {e}")
        raise


def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
    """
    Generic query executor with error handling.
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: Return single row
        fetch_all: Return all rows
    
    Returns:
        Query result or None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity constraint violated: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Query failed: {query[:100]}... Error: {e}")
        raise

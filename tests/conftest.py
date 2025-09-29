# tests/conftest.py

import pytest
import sqlite3
import os
from src import database
from src.models import user as user_model
from src.models import table as table_model
from src.models import registration as registration_model

@pytest.fixture(scope="function")
def test_db():
    """Fixture to set up an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Calcola il percorso assoluto dello schema dalla migration principale
    schema_path = os.path.join(os.path.dirname(__file__), "..", "db", "migrations", "20250926122852_initial_schema.sql")
    # Carica solo la parte di migrate:up
    with open(schema_path, "r") as f:
        sql = f.read()
    up_sql = sql.split("-- migrate:down")[0]  # Prende solo la parte prima di migrate:down
    conn.executescript(up_sql)

    # Patch the get_db_connection function in each model
    original_get_db_connection = database.get_db_connection
    user_model.get_db_connection = lambda: conn
    table_model.get_db_connection = lambda: conn
    registration_model.get_db_connection = lambda: conn

    yield conn

    # Cleanup
    database.get_db_connection = original_get_db_connection


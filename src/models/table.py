# src/models/table.py

"""
Table model and CRUD functions.
"""

from src.database import get_db_connection


def create_table(
    master_id, type, game, name, max_players, description, image, num_sessions
):
    """Creates a new table in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tables (master_id, type, game, name, max_players, description, image, num_sessions) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (master_id, type, game, name, max_players, description, image, num_sessions),
    )
    conn.commit()
    conn.close()


def get_active_tables():
    """Retrieves all active tables from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tables WHERE active = 1")
    tables = cursor.fetchall()
    conn.close()
    return tables


def get_all_tables():
    """Retrieves all tables from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tables")
    tables = cursor.fetchall()
    conn.close()
    return tables


def get_table_by_id(table_id):
    """Retrieves a table from the database by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
    table = cursor.fetchone()
    conn.close()
    return table


def update_table_status(table_id, active):
    """Updates the status of a table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tables SET active = ? WHERE id = ?", (active, table_id))
    conn.commit()
    conn.close()


def update_table(table_id, description, max_players):
    """Updates a table's description and max players."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tables SET description = ?, max_players = ? WHERE id = ?",
        (description, max_players, table_id),
    )
    conn.commit()
    conn.close()


def get_active_campaigns_by_master(master_id):
    """Retrieves all active campaigns for a given master."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tables WHERE master_id = ? AND type = 'campaign' AND active = 1",
        (master_id,),
    )
    tables = cursor.fetchall()
    conn.close()
    return tables


def get_tables_by_master_id(master_id):
    """Retrieves all tables for a given master from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tables WHERE master_id = ?", (master_id,))
    tables = cursor.fetchall()
    return tables


def get_inactive_campaigns_by_master(master_id):
    """Retrieves all inactive campaigns for a given master."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tables WHERE master_id = ? AND type = 'campaign' AND active = 0",
        (master_id,),
    )
    tables = cursor.fetchall()
    conn.close()
    return tables

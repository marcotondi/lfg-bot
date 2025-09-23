# src/models/registration.py

"""
Registration model and CRUD functions.
"""

from src.database import get_db_connection

def create_registration(table_id, user_id):
    """Creates a new registration or reactivates an existing one."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if a registration already exists
    cursor.execute("SELECT id, is_active FROM registrations WHERE table_id = ? AND user_id = ?", (table_id, user_id))
    registration = cursor.fetchone()
    
    if registration:
        # If it exists and is inactive, reactivate it
        if not registration["is_active"]:
            cursor.execute("UPDATE registrations SET is_active = TRUE WHERE id = ?", (registration["id"],))
    else:
        # Otherwise, create a new one
        cursor.execute(
            "INSERT INTO registrations (table_id, user_id) VALUES (?, ?)",
            (table_id, user_id),
        )
    
    conn.commit()
    conn.close()

def unjoin_registration(table_id, user_id):
    """Logically deletes a registration by setting is_active to FALSE."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE registrations SET is_active = FALSE WHERE table_id = ? AND user_id = ?",
        (table_id, user_id),
    )
    conn.commit()
    conn.close()

def get_registrations_count(table_id):
    """Gets the number of active registrations for a table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM registrations WHERE table_id = ? AND is_active = TRUE", (table_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_registration(table_id, user_id):
    """Gets an active registration for a user and a table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE table_id = ? AND user_id = ? AND is_active = TRUE", (table_id, user_id))
    registration = cursor.fetchone()
    conn.close()
    return registration

def get_registrations_for_table(table_id):
    """Gets all active registrations for a table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.first_name, u.last_name
        FROM registrations r
        JOIN users u ON r.user_id = u.id
        WHERE r.table_id = ? AND r.is_active = TRUE
    """, (table_id,))
    registrations = cursor.fetchall()
    conn.close()
    return registrations

def get_any_registration(table_id, user_id):
    """Gets a registration for a user and a table, regardless of active status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations WHERE table_id = ? AND user_id = ?", (table_id, user_id))
    registration = cursor.fetchone()
    conn.close()
    return registration

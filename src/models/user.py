# src/models/user.py

"""
User model and CRUD functions.
"""

from src.database import get_db_connection

def create_user(telegram_id, username, first_name, last_name):
    """Creates a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
        (telegram_id, username, first_name, last_name),
    )
    conn.commit()
    conn.close()

def get_user(telegram_id):
    """Retrieves a user from the database by their Telegram ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    """Retrieves all users from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def mute_user(telegram_id, mute):
    """Mutes or unmutes a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mute = ? WHERE telegram_id = ?", (mute, telegram_id))
    conn.commit()
    conn.close()

def set_master(telegram_id, is_master):
    """Sets or unsets a user as a master."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_master = ? WHERE telegram_id = ?", (is_master, telegram_id))
    conn.commit()
    conn.close()

def set_admin(telegram_id, is_admin):
    """Sets or unsets a user as an admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = ? WHERE telegram_id = ?", (is_admin, telegram_id))
    conn.commit()
    conn.close()

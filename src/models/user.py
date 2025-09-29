# src/models/user.py
"""
User model and CRUD functions.
"""

import logging
from typing import Optional, List, Tuple
from sqlite3 import IntegrityError, Row
from src.database import get_db_connection

logger = logging.getLogger(__name__)


class UserError(Exception):
    """Base exception for user operations."""
    pass


class UserAlreadyExistsError(UserError):
    """Raised when trying to create a user that already exists."""
    pass


def create_user(
    telegram_id: int, 
    username: Optional[str], 
    first_name: Optional[str], 
    last_name: Optional[str]
) -> int:
    """
    Creates a new user in the database.
    
    Args:
        telegram_id: Unique Telegram user ID
        username: Telegram username (can be None)
        first_name: User's first name
        last_name: User's last name
    
    Returns:
        The row ID of the created user
        
    Raises:
        UserAlreadyExistsError: If user already exists
        ValueError: If telegram_id is invalid
    """
    if not telegram_id or telegram_id <= 0:
        raise ValueError("Invalid telegram_id")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, username, first_name, last_name),
            )
            logger.info(f"Created user: telegram_id={telegram_id}, username={username}")
            return cursor.lastrowid
    except IntegrityError as e:
        logger.warning(f"User already exists: telegram_id={telegram_id}")
        raise UserAlreadyExistsError(f"User {telegram_id} already exists") from e


def get_user(telegram_id: int) -> Optional[Row]:
    """
    Retrieves a user from the database by their Telegram ID.
    
    Args:
        telegram_id: Unique Telegram user ID
        
    Returns:
        User row or None if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Failed to get user {telegram_id}: {e}")
        raise


def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> Tuple[Row, bool]:
    """
    Gets an existing user or creates a new one.
    
    Returns:
        Tuple of (user_row, was_created)
    """
    user = get_user(telegram_id)
    if user:
        return user, False
    
    try:
        create_user(telegram_id, username, first_name, last_name)
        user = get_user(telegram_id)
        return user, True
    except UserAlreadyExistsError:
        # Race condition: another process created the user
        user = get_user(telegram_id)
        return user, False


def get_all_users() -> List[Row]:
    """
    Retrieves all users from the database.
    
    Returns:
        List of user rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to get all users: {e}")
        raise


def update_user_field(telegram_id: int, field: str, value) -> bool:
    """
    Generic function to update a single user field.
    
    Args:
        telegram_id: User's Telegram ID
        field: Column name to update
        value: New value
        
    Returns:
        True if user was updated, False if not found
    """
    allowed_fields = {"mute", "is_master", "is_admin", "username", "first_name", "last_name"}
    if field not in allowed_fields:
        raise ValueError(f"Field '{field}' cannot be updated")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Using parameterized query for value, but field name must be validated above
            cursor.execute(
                f"UPDATE users SET {field} = ? WHERE telegram_id = ?",
                (value, telegram_id)
            )
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"Updated user {telegram_id}: {field}={value}")
            else:
                logger.warning(f"User {telegram_id} not found for update")
                
            return updated
    except Exception as e:
        logger.error(f"Failed to update user {telegram_id}: {e}")
        raise


def mute_user(telegram_id: int, mute: bool) -> bool:
    """
    Mutes or unmutes a user.
    
    Args:
        telegram_id: User's Telegram ID
        mute: True to mute, False to unmute
        
    Returns:
        True if successful, False if user not found
    """
    return update_user_field(telegram_id, "mute", int(mute))


def set_master(telegram_id: int, is_master: bool) -> bool:
    """
    Sets or unsets a user as a master.
    
    Args:
        telegram_id: User's Telegram ID
        is_master: True to set as master, False to remove
        
    Returns:
        True if successful, False if user not found
    """
    return update_user_field(telegram_id, "is_master", int(is_master))


def set_admin(telegram_id: int, is_admin: bool) -> bool:
    """
    Sets or unsets a user as an admin.
    
    Args:
        telegram_id: User's Telegram ID
        is_admin: True to set as admin, False to remove
        
    Returns:
        True if successful, False if user not found
    """
    return update_user_field(telegram_id, "is_admin", int(is_admin))


def delete_user(telegram_id: int) -> bool:
    """
    Deletes a user from the database.
    
    Args:
        telegram_id: User's Telegram ID
        
    Returns:
        True if user was deleted, False if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            deleted = cursor.rowcount > 0
            
            if deleted:
                logger.info(f"Deleted user: telegram_id={telegram_id}")
            else:
                logger.warning(f"User {telegram_id} not found for deletion")
                
            return deleted
    except Exception as e:
        logger.error(f"Failed to delete user {telegram_id}: {e}")
        raise
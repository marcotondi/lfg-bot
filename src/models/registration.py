# src/models/registration.py
"""
Registration model and CRUD functions.
"""

import logging
from typing import Optional, List, Tuple
from sqlite3 import IntegrityError, Row
from src.database import get_db_connection

logger = logging.getLogger(__name__)


class RegistrationError(Exception):
    """Base exception for registration operations."""
    pass


class RegistrationAlreadyExistsError(RegistrationError):
    """Raised when trying to create a duplicate active registration."""
    pass


class TableFullError(RegistrationError):
    """Raised when trying to register to a full table."""
    pass


class RegistrationNotFoundError(RegistrationError):
    """Raised when a registration is not found."""
    pass


def create_registration(table_id: int, user_id: int) -> Tuple[int, bool]:
    """
    Creates a new registration or reactivates an existing one.
    
    Args:
        table_id: Table ID
        user_id: User ID (internal DB id, not telegram_id)
        
    Returns:
        Tuple of (registration_id, was_reactivated)
        - registration_id: The ID of the registration
        - was_reactivated: True if existing registration was reactivated, False if new
        
    Raises:
        RegistrationAlreadyExistsError: If active registration already exists
        IntegrityError: If foreign key constraints fail
        TableFullError: If table is at maximum capacity
    """
    if not table_id or table_id <= 0:
        raise ValueError("Invalid table_id")
    
    if not user_id or user_id <= 0:
        raise ValueError("Invalid user_id")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if registration already exists
            cursor.execute(
                "SELECT id, is_active FROM registrations WHERE table_id = ? AND user_id = ?",
                (table_id, user_id)
            )
            registration = cursor.fetchone()
            
            if registration:
                if registration["is_active"]:
                    logger.warning(
                        f"Active registration already exists: table_id={table_id}, user_id={user_id}"
                    )
                    raise RegistrationAlreadyExistsError(
                        f"User {user_id} is already registered to table {table_id}"
                    )
                
                # Reactivate inactive registration
                cursor.execute(
                    "UPDATE registrations SET is_active = 1 WHERE id = ?",
                    (registration["id"],)
                )
                logger.info(
                    f"Reactivated registration: id={registration['id']}, "
                    f"table_id={table_id}, user_id={user_id}"
                )
                return registration["id"], True
            
            # Check if table is full before creating new registration
            cursor.execute(
                """
                SELECT t.max_players, COUNT(r.id) as current_players
                FROM tables t
                LEFT JOIN registrations r ON t.id = r.table_id AND r.is_active = 1
                WHERE t.id = ?
                GROUP BY t.id
                """,
                (table_id,)
            )
            table_info = cursor.fetchone()
            
            if not table_info:
                raise RegistrationError(f"Table {table_id} not found")
            
            if table_info["current_players"] >= table_info["max_players"]:
                logger.warning(
                    f"Table {table_id} is full: {table_info['current_players']}/{table_info['max_players']}"
                )
                raise TableFullError(
                    f"Table {table_id} is full ({table_info['max_players']} players)"
                )
            
            # Create new registration
            cursor.execute(
                "INSERT INTO registrations (table_id, user_id, is_active) VALUES (?, ?, 1)",
                (table_id, user_id),
            )
            registration_id = cursor.lastrowid
            
            if registration_id is None:
                logger.error(
                    f"Failed to create registration: lastrowid is None for table_id={table_id}, user_id={user_id}"
                )
                raise RegistrationError("Failed to create registration: registration_id is None")
            logger.info(
                f"Created registration: id={registration_id}, table_id={table_id}, user_id={user_id}"
            )
            return registration_id, False
            
    except IntegrityError as e:
        logger.error(
            f"Foreign key constraint failed for registration: "
            f"table_id={table_id}, user_id={user_id}"
        )
        raise RegistrationError(
            f"Table {table_id} or User {user_id} does not exist"
        ) from e
    except (RegistrationAlreadyExistsError, TableFullError):
        raise
    except Exception as e:
        logger.error(f"Failed to create registration: {e}")
        raise


def unjoin_registration(table_id: int, user_id: int) -> bool:
    """
    Logically deletes a registration by setting is_active to FALSE.
    
    Args:
        table_id: Table ID
        user_id: User ID
        
    Returns:
        True if registration was deactivated, False if not found or already inactive
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE registrations SET is_active = 0 WHERE table_id = ? AND user_id = ? AND is_active = 1",
                (table_id, user_id),
            )
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"Deactivated registration: table_id={table_id}, user_id={user_id}")
            else:
                logger.warning(
                    f"No active registration found to deactivate: "
                    f"table_id={table_id}, user_id={user_id}"
                )
            
            return updated
    except Exception as e:
        logger.error(f"Failed to unjoin registration: {e}")
        raise


def get_registrations_count(table_id: int) -> int:
    """
    Gets the number of active registrations for a table.
    
    Args:
        table_id: Table ID
        
    Returns:
        Number of active registrations
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM registrations WHERE table_id = ? AND is_active = 1",
                (table_id,)
            )
            result = cursor.fetchone()
            count = result["count"] if result else 0
            logger.debug(f"Table {table_id} has {count} active registrations")
            return count
    except Exception as e:
        logger.error(f"Failed to get registration count for table {table_id}: {e}")
        raise


def get_registration(table_id: int, user_id: int) -> Optional[Row]:
    """
    Gets an active registration for a user and a table.
    
    Args:
        table_id: Table ID
        user_id: User ID
        
    Returns:
        Registration row or None if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM registrations WHERE table_id = ? AND user_id = ? AND is_active = 1",
                (table_id, user_id)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(
            f"Failed to get registration: table_id={table_id}, user_id={user_id}, error={e}"
        )
        raise


def get_registrations_for_table(table_id: int) -> List[Row]:
    """
    Gets all active registrations for a table with user details.
    
    Args:
        table_id: Table ID
        
    Returns:
        List of rows with user information (username, first_name, last_name, user_id)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    r.id as registration_id,
                    r.user_id,
                    r.created_at as registered_at,
                    u.telegram_id,
                    u.username, 
                    u.first_name, 
                    u.last_name
                FROM registrations r
                JOIN users u ON r.user_id = u.id
                WHERE r.table_id = ? AND r.is_active = 1
                ORDER BY r.created_at ASC
                """,
                (table_id,)
            )
            registrations = cursor.fetchall()
            logger.debug(f"Retrieved {len(registrations)} registrations for table {table_id}")
            return registrations
    except Exception as e:
        logger.error(f"Failed to get registrations for table {table_id}: {e}")
        raise


def get_any_registration(table_id: int, user_id: int) -> Optional[Row]:
    """
    Gets a registration for a user and a table, regardless of active status.
    
    Args:
        table_id: Table ID
        user_id: User ID
        
    Returns:
        Registration row or None if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM registrations WHERE table_id = ? AND user_id = ?",
                (table_id, user_id)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(
            f"Failed to get any registration: table_id={table_id}, user_id={user_id}, error={e}"
        )
        raise


def is_user_registered(table_id: int, user_id: int) -> bool:
    """
    Checks if a user is actively registered to a table.
    
    Args:
        table_id: Table ID
        user_id: User ID
        
    Returns:
        True if user is registered, False otherwise
    """
    registration = get_registration(table_id, user_id)
    return registration is not None


def get_user_registrations(user_id: int, active_only: bool = True) -> List[Row]:
    """
    Gets all tables a user is registered to.
    
    Args:
        user_id: User ID
        active_only: If True, only return active registrations
        
    Returns:
        List of rows with table information
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute(
                    """
                    SELECT 
                        t.*,
                        r.created_at as registered_at,
                        r.is_active
                    FROM registrations r
                    JOIN tables t ON r.table_id = t.id
                    WHERE r.user_id = ? AND r.is_active = 1
                    ORDER BY r.created_at DESC
                    """,
                    (user_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT 
                        t.*,
                        r.created_at as registered_at,
                        r.is_active
                    FROM registrations r
                    JOIN tables t ON r.table_id = t.id
                    WHERE r.user_id = ?
                    ORDER BY r.created_at DESC
                    """,
                    (user_id,)
                )
            
            registrations = cursor.fetchall()
            logger.debug(f"User {user_id} has {len(registrations)} registrations")
            return registrations
    except Exception as e:
        logger.error(f"Failed to get registrations for user {user_id}: {e}")
        raise


def delete_registration(table_id: int, user_id: int) -> bool:
    """
    Permanently deletes a registration from the database.
    WARNING: This is a hard delete. Consider using unjoin_registration() instead.
    
    Args:
        table_id: Table ID
        user_id: User ID
        
    Returns:
        True if registration was deleted, False if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM registrations WHERE table_id = ? AND user_id = ?",
                (table_id, user_id)
            )
            deleted = cursor.rowcount > 0
            
            if deleted:
                logger.warning(
                    f"HARD DELETE: Permanently deleted registration: "
                    f"table_id={table_id}, user_id={user_id}"
                )
            else:
                logger.warning(
                    f"No registration found to delete: table_id={table_id}, user_id={user_id}"
                )
            
            return deleted
    except Exception as e:
        logger.error(f"Failed to delete registration: {e}")
        raise


def delete_all_registrations_for_table(table_id: int) -> int:
    """
    Permanently deletes all registrations for a table.
    WARNING: This is a hard delete, usually triggered by table deletion via CASCADE.
    
    Args:
        table_id: Table ID
        
    Returns:
        Number of registrations deleted
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM registrations WHERE table_id = ?", (table_id,))
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.warning(
                    f"HARD DELETE: Permanently deleted {deleted_count} registrations for table {table_id}"
                )
            
            return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete registrations for table {table_id}: {e}")
        raise


def get_table_capacity_info(table_id: int) -> dict:
    """
    Gets detailed capacity information for a table.
    
    Args:
        table_id: Table ID
        
    Returns:
        Dictionary with keys:
        - max_players: Maximum capacity
        - current_players: Current active registrations
        - available_spots: Remaining spots
        - is_full: Boolean indicating if table is full
        - fill_percentage: Percentage of capacity filled (0-100)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    t.max_players,
                    COUNT(r.id) as current_players
                FROM tables t
                LEFT JOIN registrations r ON t.id = r.table_id AND r.is_active = 1
                WHERE t.id = ?
                GROUP BY t.id, t.max_players
                """,
                (table_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise RegistrationError(f"Table {table_id} not found")
            
            max_players = result["max_players"]
            current_players = result["current_players"]
            available_spots = max_players - current_players
            is_full = current_players >= max_players
            fill_percentage = (current_players / max_players * 100) if max_players > 0 else 0
            
            return {
                "max_players": max_players,
                "current_players": current_players,
                "available_spots": available_spots,
                "is_full": is_full,
                "fill_percentage": round(fill_percentage, 1)
            }
    except Exception as e:
        logger.error(f"Failed to get capacity info for table {table_id}: {e}")
        raise
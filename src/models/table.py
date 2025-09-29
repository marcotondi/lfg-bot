# src/models/table.py
"""
Table model and CRUD functions.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlite3 import IntegrityError, Row
from src.database import get_db_connection

logger = logging.getLogger(__name__)


class TableError(Exception):
    """Base exception for table operations."""
    pass


class TableNotFoundError(TableError):
    """Raised when a table is not found."""
    pass


class InvalidTableDataError(TableError):
    """Raised when table data is invalid."""
    pass


def create_table(
    master_id: int,
    type: str,
    game: str,
    name: str,
    max_players: int,
    description: Optional[str] = None,
    image: Optional[str] = None,
    num_sessions: int = 0
) -> int:
    """
    Creates a new table in the database.
    
    Args:
        master_id: Telegram ID of the master
        type: Table type ('campaign', 'oneshot', etc.)
        game: Game system name
        name: Table name
        max_players: Maximum number of players
        description: Optional table description
        image: Optional image URL/path
        num_sessions: Number of sessions (default: 0)
    
    Returns:
        The row ID of the created table
        
    Raises:
        InvalidTableDataError: If validation fails
        IntegrityError: If foreign key constraint fails
    """
    # Validation
    if not master_id or master_id <= 0:
        raise InvalidTableDataError("Invalid master_id")
    
    if not name or not name.strip():
        raise InvalidTableDataError("Table name cannot be empty")
    
    if max_players <= 0:
        raise InvalidTableDataError("max_players must be positive")
    
    valid_types = {'campaign', 'oneshot'}
    if type not in valid_types:
        raise InvalidTableDataError(f"Invalid type. Must be one of: {valid_types}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tables 
                (master_id, type, game, name, max_players, description, image, num_sessions) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (master_id, type, game, name, max_players, description, image, num_sessions),
            )
            table_id = cursor.lastrowid
            logger.info(
                f"Created table: id={table_id}, name={name}, master_id={master_id}, type={type}"
            )
            return table_id
    except IntegrityError as e:
        logger.error(f"Failed to create table: foreign key violation (master_id={master_id})")
        raise TableError(f"Master with ID {master_id} does not exist") from e
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise


def get_active_tables() -> List[Row]:
    """
    Retrieves all active tables from the database.
    
    Returns:
        List of active table rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tables WHERE active = 1 ORDER BY created_at DESC"
            )
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} active tables")
            return tables
    except Exception as e:
        logger.error(f"Failed to get active tables: {e}")
        raise


def get_all_tables() -> List[Row]:
    """
    Retrieves all tables from the database.
    
    Returns:
        List of all table rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tables ORDER BY created_at DESC")
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} tables")
            return tables
    except Exception as e:
        logger.error(f"Failed to get all tables: {e}")
        raise


def get_table_by_id(table_id: int) -> Optional[Row]:
    """
    Retrieves a table from the database by its ID.
    
    Args:
        table_id: Table ID
        
    Returns:
        Table row or None if not found
    """
    if not table_id or table_id <= 0:
        raise ValueError("Invalid table_id")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
            table = cursor.fetchone()
            
            if not table:
                logger.warning(f"Table not found: id={table_id}")
            
            return table
    except Exception as e:
        logger.error(f"Failed to get table {table_id}: {e}")
        raise


def update_table_field(table_id: int, field: str, value: Any) -> bool:
    """
    Generic function to update a single table field.
    
    Args:
        table_id: Table ID
        field: Column name to update
        value: New value
        
    Returns:
        True if table was updated, False if not found
        
    Raises:
        ValueError: If field is not allowed to be updated
    """
    allowed_fields = {
        "active", "description", "max_players", "name", 
        "game", "image", "num_sessions", "type"
    }
    
    if field not in allowed_fields:
        raise ValueError(f"Field '{field}' cannot be updated")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tables SET {field} = ? WHERE id = ?",
                (value, table_id)
            )
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"Updated table {table_id}: {field}={value}")
            else:
                logger.warning(f"Table {table_id} not found for update")
                
            return updated
    except Exception as e:
        logger.error(f"Failed to update table {table_id}: {e}")
        raise


def update_table_status(table_id: int, active: bool) -> bool:
    """
    Updates the status of a table.
    
    Args:
        table_id: Table ID
        active: True to activate, False to deactivate
        
    Returns:
        True if successful, False if table not found
    """
    return update_table_field(table_id, "active", int(active))


def update_table(table_id: int, description: str, max_players: int) -> bool:
    """
    Updates a table's description and max players.
    
    Args:
        table_id: Table ID
        description: New description
        max_players: New maximum number of players
        
    Returns:
        True if successful, False if table not found
        
    Raises:
        InvalidTableDataError: If max_players is invalid
    """
    if max_players <= 0:
        raise InvalidTableDataError("max_players must be positive")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tables SET description = ?, max_players = ? WHERE id = ?",
                (description, max_players, table_id),
            )
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(
                    f"Updated table {table_id}: description='{description[:50]}...', "
                    f"max_players={max_players}"
                )
            else:
                logger.warning(f"Table {table_id} not found for update")
                
            return updated
    except Exception as e:
        logger.error(f"Failed to update table {table_id}: {e}")
        raise


def update_table_full(
    table_id: int,
    updates: Dict[str, Any]
) -> bool:
    """
    Updates multiple fields of a table at once.
    
    Args:
        table_id: Table ID
        updates: Dictionary of field names and values to update
        
    Returns:
        True if successful, False if table not found
        
    Example:
        update_table_full(1, {
            'name': 'New Name',
            'max_players': 6,
            'description': 'Updated description'
        })
    """
    allowed_fields = {
        "active", "description", "max_players", "name", 
        "game", "image", "num_sessions", "type"
    }
    
    # Validate all fields
    invalid_fields = set(updates.keys()) - allowed_fields
    if invalid_fields:
        raise ValueError(f"Invalid fields: {invalid_fields}")
    
    if not updates:
        logger.warning("No fields to update")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic query
            set_clause = ", ".join(f"{field} = ?" for field in updates.keys())
            values = list(updates.values()) + [table_id]
            
            cursor.execute(
                f"UPDATE tables SET {set_clause} WHERE id = ?",
                values
            )
            updated = cursor.rowcount > 0
            
            if updated:
                logger.info(f"Updated table {table_id}: {updates}")
            else:
                logger.warning(f"Table {table_id} not found for update")
                
            return updated
    except Exception as e:
        logger.error(f"Failed to update table {table_id}: {e}")
        raise


def get_active_campaigns_by_master(master_id: int) -> List[Row]:
    """
    Retrieves all active campaigns for a given master.
    
    Args:
        master_id: Master's Telegram ID
        
    Returns:
        List of active campaign rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tables 
                WHERE master_id = ? AND type = 'campaign' AND active = 1
                ORDER BY created_at DESC
                """,
                (master_id,),
            )
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} active campaigns for master {master_id}")
            return tables
    except Exception as e:
        logger.error(f"Failed to get active campaigns for master {master_id}: {e}")
        raise


def get_tables_by_master_id(master_id: int) -> List[Row]:
    """
    Retrieves all tables for a given master from the database.
    
    Args:
        master_id: Master's Telegram ID
        
    Returns:
        List of table rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tables WHERE master_id = ? ORDER BY created_at DESC",
                (master_id,)
            )
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} tables for master {master_id}")
            return tables
    except Exception as e:
        logger.error(f"Failed to get tables for master {master_id}: {e}")
        raise


def get_inactive_campaigns_by_master(master_id: int) -> List[Row]:
    """
    Retrieves all inactive campaigns for a given master.
    
    Args:
        master_id: Master's Telegram ID
        
    Returns:
        List of inactive campaign rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tables 
                WHERE master_id = ? AND type = 'campaign' AND active = 0
                ORDER BY created_at DESC
                """,
                (master_id,),
            )
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} inactive campaigns for master {master_id}")
            return tables
    except Exception as e:
        logger.error(f"Failed to get inactive campaigns for master {master_id}: {e}")
        raise


def get_tables_by_type(table_type: str, active_only: bool = False) -> List[Row]:
    """
    Retrieves all tables of a specific type.
    
    Args:
        table_type: Type of table ('campaign', 'oneshot', etc.)
        active_only: If True, only return active tables
        
    Returns:
        List of table rows
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute(
                    """
                    SELECT * FROM tables 
                    WHERE type = ? AND active = 1
                    ORDER BY created_at DESC
                    """,
                    (table_type,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM tables WHERE type = ? ORDER BY created_at DESC",
                    (table_type,)
                )
            
            tables = cursor.fetchall()
            logger.debug(f"Retrieved {len(tables)} tables of type '{table_type}'")
            return tables
    except Exception as e:
        logger.error(f"Failed to get tables by type '{table_type}': {e}")
        raise


def delete_table(table_id: int) -> bool:
    """
    Deletes a table from the database.
    WARNING: This will also delete all related registrations due to foreign key constraints.
    
    Args:
        table_id: Table ID
        
    Returns:
        True if table was deleted, False if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tables WHERE id = ?", (table_id,))
            deleted = cursor.rowcount > 0
            
            if deleted:
                logger.warning(f"Deleted table: id={table_id} (and all related registrations)")
            else:
                logger.warning(f"Table {table_id} not found for deletion")
                
            return deleted
    except Exception as e:
        logger.error(f"Failed to delete table {table_id}: {e}")
        raise


def get_table_with_player_count(table_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves a table with the current number of registered players.
    
    Args:
        table_id: Table ID
        
    Returns:
        Dictionary with table data and player_count, or None if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.*, COUNT(r.user_id) as player_count
                FROM tables t
                LEFT JOIN registrations r ON t.id = r.table_id
                WHERE t.id = ?
                GROUP BY t.id
                """,
                (table_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Failed to get table with player count {table_id}: {e}")
        raise


def is_table_full(table_id: int) -> bool:
    """
    Checks if a table has reached its maximum capacity.
    
    Args:
        table_id: Table ID
        
    Returns:
        True if table is full, False otherwise
        
    Raises:
        TableNotFoundError: If table doesn't exist
    """
    table_data = get_table_with_player_count(table_id)
    
    if not table_data:
        raise TableNotFoundError(f"Table {table_id} not found")
    
    return table_data['player_count'] >= table_data['max_players']
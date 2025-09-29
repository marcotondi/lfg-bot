# tests/models/test_table_model.py

import pytest
from src.models import table as table_model
from src.models import user as user_model

def test_create_table(test_db):
    """
    Tests that a table can be created.
    """
    # First, create a user to be the master of the table
    user_model.create_user(1, "testuser", "Test", "User")
    
    table_model.create_table(
        master_id=1,
        type="one-shot",
        game="D&D 5e",
        name="Test Table",
        max_players=5,
        description="A test table.",
        image="test.png",
        num_sessions=1
    )
    
    table = test_db.execute("SELECT * FROM tables WHERE name = ?", ("Test Table",)).fetchone()
    
    assert table is not None
    assert table["master_id"] == 1
    assert table["game"] == "D&D 5e"
    assert table["max_players"] == 5

def test_get_active_tables(test_db):
    """
    Tests that active tables can be retrieved.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Active Table", 5, "A test table.", "test.png", 1)
    table_model.create_table(1, "campaign", "Pathfinder", "Inactive Table", 4, "Another test table.", "test2.png", 10)
    table_model.update_table_status(2, 0)
    
    active_tables = table_model.get_active_tables()
    
    assert len(active_tables) == 1
    assert active_tables[0]["name"] == "Active Table"

def test_get_all_tables(test_db):
    """
    Tests that all tables can be retrieved.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Active Table", 5, "A test table.", "test.png", 1)
    table_model.create_table(1, "campaign", "Pathfinder", "Inactive Table", 4, "Another test table.", "test2.png", 10)
    
    all_tables = table_model.get_all_tables()
    
    assert len(all_tables) == 2

def test_get_table_by_id(test_db):
    """
    Tests that a table can be retrieved by its ID.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    table = table_model.get_table_by_id(1)
    
    assert table is not None
    assert table["name"] == "Test Table"

def test_update_table_status(test_db):
    """
    Tests that a table's status can be updated.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    table_model.update_table_status(1, 0)
    
    table = table_model.get_table_by_id(1)
    assert table["active"] == 0

def test_update_table(test_db):
    """
    Tests that a table can be updated.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    table_model.update_table(1, "An updated description.", 6)
    
    table = table_model.get_table_by_id(1)
    assert table["description"] == "An updated description."
    assert table["max_players"] == 6

def test_get_active_campaigns_by_master(test_db):
    """
    Tests that active campaigns can be retrieved for a given master.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "campaign", "D&D 5e", "Active Campaign", 5, "A test campaign.", "test.png", 10)
    table_model.create_table(1, "one-shot", "D&D 5e", "Active One-Shot", 5, "A test one-shot.", "test.png", 1)
    table_model.create_table(1, "campaign", "Pathfinder", "Inactive Campaign", 4, "Another test campaign.", "test2.png", 10)
    table_model.update_table_status(3, 0)
    
    active_campaigns = table_model.get_active_campaigns_by_master(1)
    
    assert len(active_campaigns) == 1
    assert active_campaigns[0]["name"] == "Active Campaign"

def test_get_tables_by_master_id(test_db):
    """
    Tests that all tables for a given master can be retrieved.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    user_model.create_user(2, "anotheruser", "Another", "User")
    table_model.create_table(1, "campaign", "D&D 5e", "Campaign 1", 5, "A test campaign.", "test.png", 10)
    table_model.create_table(1, "one-shot", "D&D 5e", "One-Shot 1", 5, "A test one-shot.", "test.png", 1)
    table_model.create_table(2, "campaign", "Pathfinder", "Campaign 2", 4, "Another test campaign.", "test2.png", 10)
    
    master_tables = table_model.get_tables_by_master_id(1)
    
    assert len(master_tables) == 2

def test_get_inactive_campaigns_by_master(test_db):
    """
    Tests that inactive campaigns can be retrieved for a given master.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "campaign", "D&D 5e", "Active Campaign", 5, "A test campaign.", "test.png", 10)
    table_model.create_table(1, "campaign", "Pathfinder", "Inactive Campaign", 4, "Another test campaign.", "test2.png", 10)
    table_model.update_table_status(2, 0)
    
    inactive_campaigns = table_model.get_inactive_campaigns_by_master(1)
    
    assert len(inactive_campaigns) == 1
    assert inactive_campaigns[0]["name"] == "Inactive Campaign"

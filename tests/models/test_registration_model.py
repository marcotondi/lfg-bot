# tests/models/test_registration_model.py

import pytest
from src.models import registration as registration_model
from src.models import table as table_model
from src.models import user as user_model

def test_create_registration(test_db):
    """
    Tests that a registration can be created.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    registration_model.create_registration(1, 1)
    
    registration = test_db.execute("SELECT * FROM registrations WHERE table_id = ? AND user_id = ?", (1, 1)).fetchone()
    
    assert registration is not None
    assert registration["is_active"] == 1

def test_unjoin_registration(test_db):
    """
    Tests that a registration can be logically deleted.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    registration_model.create_registration(1, 1)
    
    registration_model.unjoin_registration(1, 1)
    
    registration = registration_model.get_registration(1, 1)
    assert registration is None
    
    any_registration = registration_model.get_any_registration(1, 1)
    assert any_registration is not None
    assert any_registration["is_active"] == 0

def test_get_registrations_count(test_db):
    """
    Tests that the number of active registrations for a table can be retrieved.
    """
    user_model.create_user(1, "testuser1", "Test1", "User1")
    user_model.create_user(2, "testuser2", "Test2", "User2")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    registration_model.create_registration(1, 1)
    registration_model.create_registration(1, 2)
    
    count = registration_model.get_registrations_count(1)
    assert count == 2
    
    registration_model.unjoin_registration(1, 1)
    
    count = registration_model.get_registrations_count(1)
    assert count == 1

def test_get_registration(test_db):
    """
    Tests that an active registration can be retrieved.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    registration_model.create_registration(1, 1)
    
    registration = registration_model.get_registration(1, 1)
    assert registration is not None
    
    registration_model.unjoin_registration(1, 1)
    
    registration = registration_model.get_registration(1, 1)
    assert registration is None

def test_get_registrations_for_table(test_db):
    """
    Tests that all active registrations for a table can be retrieved.
    """
    user_model.create_user(1, "testuser1", "Test1", "User1")
    user_model.create_user(2, "testuser2", "Test2", "User2")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    
    registration_model.create_registration(1, 1)
    registration_model.create_registration(1, 2)
    
    registrations = registration_model.get_registrations_for_table(1)
    
    assert len(registrations) == 2
    assert registrations[0]["username"] == "testuser1"
    assert registrations[1]["username"] == "testuser2"

def test_get_any_registration(test_db):
    """
    Tests that a registration can be retrieved regardless of its active status.
    """
    user_model.create_user(1, "testuser", "Test", "User")
    table_model.create_table(1, "one-shot", "D&D 5e", "Test Table", 5, "A test table.", "test.png", 1)
    registration_model.create_registration(1, 1)
    registration_model.unjoin_registration(1, 1)
    
    registration = registration_model.get_any_registration(1, 1)
    
    assert registration is not None
    assert registration["is_active"] == 0

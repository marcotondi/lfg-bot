# tests/models/test_user_model.py

from src.models import user as user_model

# La fixture `test_db` viene iniettata automaticamente da conftest.py
def test_create_and_get_user(test_db):
    """
    Tests creating a user and then retrieving it.
    """
    # Dati di test
    telegram_id = 12345
    username = "testuser"
    first_name = "Test"
    last_name = "User"

    # 1. Crea l'utente
    user_model.create_user(telegram_id, username, first_name, last_name)

    # 2. Recupera l'utente
    retrieved_user = user_model.get_user(telegram_id)

    # 3. Verifica che l'utente recuperato non sia None e che i dati siano corretti
    assert retrieved_user is not None
    assert retrieved_user["telegram_id"] == telegram_id
    assert retrieved_user["username"] == username
    assert retrieved_user["first_name"] == first_name
    assert retrieved_user["last_name"] == last_name
    assert retrieved_user["is_admin"] == 0
    assert retrieved_user["is_master"] == 0

def test_get_non_existent_user(test_db):
    """
    Tests that getting a non-existent user returns None.
    """
    retrieved_user = user_model.get_user(99999)
    assert retrieved_user is None

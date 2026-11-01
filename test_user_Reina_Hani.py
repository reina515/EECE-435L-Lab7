import pytest
from flask import json

import database
from database import (
    DEFAULT_USERS,
    create_db_table,
    insert_user,
    get_users,
    get_user_by_id,
    update_user,
    delete_user,
)
from app import app


# Gives every test its own empty temporary database so the real one is never touched.
@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "test_database.db"))
    yield


# Sets up the database the same way the app does on its first run.
@pytest.fixture
def seeded_db():
    create_db_table()


# Gives a Flask test client so we can call the API without running the server.
@pytest.fixture
def client(seeded_db):
    app.config["TESTING"] = True
    return app.test_client()


# A sample user to add in the insert tests.
@pytest.fixture
def new_user():
    return {
        "name": "Test User",
        "email": "test.user@aub.edu.lb",
        "phone": "70111222",
        "address": "Hamra Street",
        "country": "Lebanon",
    }


# Returns a copy of the user without the id, so we can compare it to the data we sent.
def strip_id(user):
    return {k: v for k, v in user.items() if k != "user_id"}


# Checks that the first run creates the table and adds the default users.
def test_database_created_with_specified_users():
    assert get_users() == []
    create_db_table()
    users = get_users()
    assert len(users) == len(DEFAULT_USERS)
    assert [strip_id(u) for u in users] == DEFAULT_USERS
    assert [u["user_id"] for u in users] == [1, 2, 3]


# Checks that running the app again doesn't add the default users a second time.
def test_database_not_seeded_twice():
    create_db_table()
    create_db_table()
    assert len(get_users()) == len(DEFAULT_USERS)


# Checks that a new user is saved and gets the next id.
def test_insert_user(seeded_db, new_user):
    inserted = insert_user(new_user)
    assert inserted["user_id"] == len(DEFAULT_USERS) + 1
    assert strip_id(inserted) == new_user
    assert len(get_users()) == len(DEFAULT_USERS) + 1


# Checks that a user with missing fields is rejected and nothing is saved.
def test_insert_user_missing_field_returns_empty(seeded_db):
    assert insert_user({"name": "No Email"}) == {}
    assert len(get_users()) == len(DEFAULT_USERS)


# Checks that get_users returns every user with all of their fields.
def test_get_users(seeded_db, new_user):
    insert_user(new_user)
    users = get_users()
    assert isinstance(users, list)
    assert len(users) == len(DEFAULT_USERS) + 1
    assert users[-1]["email"] == new_user["email"]
    for u in users:
        assert set(u) == {"user_id", "name", "email", "phone", "address", "country"}


# Checks that we get the right user when searching by id.
def test_get_user_by_id(seeded_db):
    user = get_user_by_id(2)
    assert user["user_id"] == 2
    assert strip_id(user) == DEFAULT_USERS[1]


# Checks that searching for an id that doesn't exist returns an empty result.
def test_get_user_by_id_not_found(seeded_db):
    assert get_user_by_id(999) == {}


# Checks that updating a user changes only that user.
def test_update_user(seeded_db):
    changes = {
        "user_id": 1,
        "name": "Reina Hani",
        "email": "reina.updated@gmail.com",
        "phone": "71000000",
        "address": "Beirut",
        "country": "Lebanon",
    }
    updated = update_user(changes)
    assert updated == changes
    assert get_user_by_id(1) == changes
    assert strip_id(get_user_by_id(2)) == DEFAULT_USERS[1]


# Checks that a deleted user is gone from the database.
def test_delete_user(seeded_db):
    result = delete_user(3)
    assert result == {"status": "User deleted successfully"}
    assert get_user_by_id(3) == {}
    assert len(get_users()) == len(DEFAULT_USERS) - 1


# Checks that GET /api/users returns 200 and the list of all users.
def test_api_get_users(client):
    response = client.get('/api/users')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == len(DEFAULT_USERS)
    assert "Reina Hani" in str(response.data)


# Checks that GET /api/users/<id> returns 200 and the right user.
def test_api_get_user(client):
    response = client.get('/api/users/1')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["user_id"] == 1
    assert strip_id(data) == DEFAULT_USERS[0]


# Checks that asking the API for a missing user returns an empty result.
def test_api_get_user_not_found(client):
    response = client.get('/api/users/999')
    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True)) == {}


# Checks that POST /api/users/add saves the user and we can read it back.
def test_api_add_user(client, new_user):
    response = client.post(
        '/api/users/add',
        data=json.dumps(new_user),
        content_type='application/json',
    )
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data["user_id"] == len(DEFAULT_USERS) + 1
    assert strip_id(data) == new_user
    check = client.get(f'/api/users/{data["user_id"]}')
    assert json.loads(check.get_data(as_text=True)) == data


# Checks that PUT /api/users/update changes the user and the change is saved.
def test_api_update_user(client):
    changes = {
        "user_id": 2,
        "name": "John Doe",
        "email": "john.doe@aub.edu.lb",
        "phone": "76999888",
        "address": "Jounieh",
        "country": "Lebanon",
    }
    response = client.put(
        '/api/users/update',
        data=json.dumps(changes),
        content_type='application/json',
    )
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data == changes
    check = client.get('/api/users/2')
    assert json.loads(check.get_data(as_text=True)) == changes


# Checks that DELETE /api/users/delete/<id> removes the user from the list.
def test_api_delete_user(client):
    response = client.delete('/api/users/delete/1')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data == {"status": "User deleted successfully"}
    remaining = json.loads(client.get('/api/users').get_data(as_text=True))
    assert len(remaining) == len(DEFAULT_USERS) - 1
    assert 1 not in [u["user_id"] for u in remaining]

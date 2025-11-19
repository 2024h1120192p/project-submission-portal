import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from services.users_service.app.main import app
from services.users_service.app.store import store
from libs.events.schemas import User

# Synchronous client for basic tests
client = TestClient(app)


class TestUserEndpoints:
    """Test FastAPI user service endpoints."""

    def test_create_user(self):
        """Test POST /users creates a new user."""
        payload = {"id": "u1", "name": "Alice", "email": "alice@test.com", "role": "student"}
        r = client.post("/users", json=payload)
        assert r.status_code == 201
        assert r.json()["id"] == "u1"
        assert r.json()["name"] == "Alice"
        assert r.json()["email"] == "alice@test.com"
        assert r.json()["role"] == "student"

    def test_get_user_success(self):
        """Test GET /users/{id} retrieves an existing user."""
        payload = {"id": "u2", "name": "Bob", "email": "bob@test.com", "role": "faculty"}
        client.post("/users", json=payload)
        
        r = client.get("/users/u2")
        assert r.status_code == 200
        assert r.json()["name"] == "Bob"
        assert r.json()["role"] == "faculty"

    def test_get_user_not_found(self):
        """Test GET /users/{id} returns 404 for non-existent user."""
        r = client.get("/users/nonexistent")
        assert r.status_code == 404

    def test_list_users_empty(self):
        """Test GET /users returns empty list when no users exist."""
        r = client.get("/users")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_users_multiple(self):
        """Test GET /users returns all users."""
        users = [
            {"id": "u1", "name": "Alice", "email": "alice@test.com", "role": "student"},
            {"id": "u2", "name": "Bob", "email": "bob@test.com", "role": "faculty"},
            {"id": "u3", "name": "Carol", "email": "carol@test.com", "role": "student"},
        ]
        for user in users:
            client.post("/users", json=user)
        
        r = client.get("/users")
        assert r.status_code == 200
        assert len(r.json()) == 3
        names = [u["name"] for u in r.json()]
        assert "Alice" in names
        assert "Bob" in names
        assert "Carol" in names

    def test_update_user_success(self):
        """Test PUT /users/{id} updates an existing user."""
        payload = {"id": "u4", "name": "Dave", "email": "dave@test.com", "role": "student"}
        client.post("/users", json=payload)
        
        updated = {"id": "u4", "name": "David", "email": "david@test.com", "role": "faculty"}
        r = client.put("/users/u4", json=updated)
        assert r.status_code == 200
        assert r.json()["name"] == "David"
        assert r.json()["email"] == "david@test.com"
        assert r.json()["role"] == "faculty"
        
        # Verify the update persisted
        r2 = client.get("/users/u4")
        assert r2.json()["name"] == "David"

    def test_update_user_not_found(self):
        """Test PUT /users/{id} returns 404 for non-existent user."""
        payload = {"id": "u5", "name": "Eve", "email": "eve@test.com", "role": "student"}
        r = client.put("/users/nonexistent", json=payload)
        assert r.status_code == 404

    def test_delete_user_success(self):
        """Test DELETE /users/{id} removes an existing user."""
        payload = {"id": "u6", "name": "Frank", "email": "frank@test.com", "role": "student"}
        client.post("/users", json=payload)
        
        r = client.delete("/users/u6")
        assert r.status_code == 200
        assert r.json()["deleted"] is True
        
        # Verify user no longer exists
        r2 = client.get("/users/u6")
        assert r2.status_code == 404

    def test_delete_user_not_found(self):
        """Test DELETE /users/{id} returns 404 for non-existent user."""
        r = client.delete("/users/nonexistent")
        assert r.status_code == 404

    def test_create_and_get_user(self):
        """Original test case - create and retrieve user."""
        payload = {"id": "1", "name": "A", "email": "a@test.com", "role": "student"}
        client.post("/users", json=payload)
        r = client.get("/users/1")
        assert r.status_code == 200
        assert r.json()["name"] == "A"


@pytest.mark.asyncio
class TestUserStore:
    """Test async UserStore CRUD operations."""

    async def test_create_and_get(self):
        """Test creating and retrieving a user from store."""
        user = User(id="s1", name="Store Test", email="store@test.com", role="student")
        await store.create(user)
        
        retrieved = await store.get("s1")
        assert retrieved is not None
        assert retrieved.name == "Store Test"
        assert retrieved.email == "store@test.com"

    async def test_get_nonexistent(self):
        """Test getting a non-existent user returns None."""
        result = await store.get("nonexistent")
        assert result is None

    async def test_list_empty(self):
        """Test listing users when store is empty."""
        users = await store.list()
        assert users == []

    async def test_list_multiple(self):
        """Test listing multiple users."""
        users = [
            User(id="s1", name="User1", email="u1@test.com", role="student"),
            User(id="s2", name="User2", email="u2@test.com", role="faculty"),
        ]
        for user in users:
            await store.create(user)
        
        all_users = await store.list()
        assert len(all_users) == 2

    async def test_update(self):
        """Test updating a user in the store."""
        user = User(id="s3", name="Original", email="orig@test.com", role="student")
        await store.create(user)
        
        updated = User(id="s3", name="Updated", email="updated@test.com", role="faculty")
        result = await store.update("s3", updated)
        
        assert result.name == "Updated"
        assert result.email == "updated@test.com"
        
        # Verify persistence
        retrieved = await store.get("s3")
        assert retrieved.name == "Updated"

    async def test_delete(self):
        """Test deleting a user from the store."""
        user = User(id="s4", name="ToDelete", email="delete@test.com", role="student")
        await store.create(user)
        
        deleted = await store.delete("s4")
        assert deleted is not None
        assert deleted.id == "s4"
        
        # Verify user is gone
        result = await store.get("s4")
        assert result is None

    async def test_delete_nonexistent(self):
        """Test deleting a non-existent user returns None."""
        result = await store.delete("nonexistent")
        assert result is None

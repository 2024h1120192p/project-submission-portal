import pytest
from unittest.mock import AsyncMock, Mock
from httpx import Response
from services.users_service.app.client import UserServiceClient
from libs.events.schemas import User


@pytest.mark.asyncio
class TestUserServiceClient:
    """Test UserServiceClient for inter-service communication."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock AsyncHTTPClient."""
        mock = Mock()
        mock.get = AsyncMock()
        mock.post = AsyncMock()
        mock.put = AsyncMock()
        mock.delete = AsyncMock()
        return mock

    @pytest.fixture
    def user_client(self, mock_http_client):
        """Create UserServiceClient with mocked HTTP client."""
        client = UserServiceClient("http://localhost:8000")
        client.client = mock_http_client
        return client

    async def test_get_user_success(self, user_client, mock_http_client):
        """Test get_user returns User when found."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "u1",
            "name": "Alice",
            "email": "alice@test.com",
            "role": "student"
        }
        mock_http_client.get.return_value = mock_response

        user = await user_client.get_user("u1")
        
        assert user is not None
        assert user.id == "u1"
        assert user.name == "Alice"
        assert user.email == "alice@test.com"
        assert user.role == "student"
        mock_http_client.get.assert_called_once_with("/users/u1")

    async def test_get_user_not_found(self, user_client, mock_http_client):
        """Test get_user returns None when user not found."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_http_client.get.return_value = mock_response

        user = await user_client.get_user("nonexistent")
        
        assert user is None
        mock_http_client.get.assert_called_once_with("/users/nonexistent")

    async def test_get_all_success(self, user_client, mock_http_client):
        """Test get_all returns list of users."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "u1", "name": "Alice", "email": "alice@test.com", "role": "student"},
            {"id": "u2", "name": "Bob", "email": "bob@test.com", "role": "faculty"}
        ]
        mock_http_client.get.return_value = mock_response

        users = await user_client.get_all()
        
        assert len(users) == 2
        assert users[0].name == "Alice"
        assert users[1].name == "Bob"
        mock_http_client.get.assert_called_once_with("/users")

    async def test_get_all_empty(self, user_client, mock_http_client):
        """Test get_all returns empty list when no users."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_http_client.get.return_value = mock_response

        users = await user_client.get_all()
        
        assert users == []

    async def test_get_all_error(self, user_client, mock_http_client):
        """Test get_all returns empty list on error."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_http_client.get.return_value = mock_response

        users = await user_client.get_all()
        
        assert users == []

    async def test_create_success(self, user_client, mock_http_client):
        """Test create returns created user."""
        user = User(id="u3", name="Carol", email="carol@test.com", role="student")
        mock_response = Mock(spec=Response)
        mock_response.status_code = 201
        mock_response.json.return_value = user.model_dump()
        mock_http_client.post.return_value = mock_response

        result = await user_client.create(user)
        
        assert result is not None
        assert result.id == "u3"
        assert result.name == "Carol"
        mock_http_client.post.assert_called_once_with("/users", json=user.model_dump())

    async def test_create_failure(self, user_client, mock_http_client):
        """Test create returns None on failure."""
        user = User(id="u4", name="Dave", email="dave@test.com", role="faculty")
        mock_response = Mock(spec=Response)
        mock_response.status_code = 400
        mock_http_client.post.return_value = mock_response

        result = await user_client.create(user)
        
        assert result is None

    async def test_update_success(self, user_client, mock_http_client):
        """Test update returns updated user."""
        user = User(id="u5", name="Eve Updated", email="eve@test.com", role="faculty")
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = user.model_dump()
        mock_http_client.put.return_value = mock_response

        result = await user_client.update("u5", user)
        
        assert result is not None
        assert result.name == "Eve Updated"
        mock_http_client.put.assert_called_once_with("/users/u5", json=user.model_dump())

    async def test_update_not_found(self, user_client, mock_http_client):
        """Test update returns None when user not found."""
        user = User(id="u6", name="Frank", email="frank@test.com", role="student")
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_http_client.put.return_value = mock_response

        result = await user_client.update("u6", user)
        
        assert result is None

    async def test_delete_success(self, user_client, mock_http_client):
        """Test delete returns True on success."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_http_client.delete.return_value = mock_response

        result = await user_client.delete("u7")
        
        assert result is True
        mock_http_client.delete.assert_called_once_with("/users/u7")

    async def test_delete_not_found(self, user_client, mock_http_client):
        """Test delete returns False when user not found."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        mock_http_client.delete.return_value = mock_response

        result = await user_client.delete("nonexistent")
        
        assert result is False

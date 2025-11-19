import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from services.submission_service.app.main import app, user_service_client, store
from services.users_service.app.client import UserServiceClient
from libs.events.schemas import User, Submission
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def clear_store():
    """Clear the store before each test."""
    store.db.clear()
    yield
    store.db.clear()


@pytest.mark.asyncio
async def test_create_and_get(async_client):
    """Test creating and retrieving a submission."""
    # Mock user service client
    mock_user = User(id="u1", name="Test User", email="test@example.com", role="student")
    
    with patch.object(user_service_client, 'get_user', new=AsyncMock(return_value=mock_user)):
        payload = {
            "id": "sub1",
            "user_id": "u1",
            "assignment_id": "a1",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "file_url": "gs://file.pdf",
            "text": "hello world"
        }

        # Create submission
        r = await async_client.post("/submissions", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["id"] == "sub1"
        assert data["user_id"] == "u1"
        assert data["assignment_id"] == "a1"

        # Get submission by ID
        r = await async_client.get("/submissions/sub1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "sub1"


@pytest.mark.asyncio
async def test_create_submission_user_not_found(async_client):
    """Test creating submission with non-existent user."""
    with patch.object(user_service_client, 'get_user', new=AsyncMock(return_value=None)):
        payload = {
            "id": "sub2",
            "user_id": "nonexistent",
            "assignment_id": "a1",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "file_url": "gs://file.pdf",
            "text": "test"
        }

        r = await async_client.post("/submissions", json=payload)
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]


@pytest.mark.asyncio
async def test_get_submissions_by_user(async_client):
    """Test retrieving all submissions for a user."""
    mock_user = User(id="u1", name="Test User", email="test@example.com", role="student")
    
    with patch.object(user_service_client, 'get_user', new=AsyncMock(return_value=mock_user)):
        # Create multiple submissions
        for i in range(3):
            payload = {
                "id": f"sub{i}",
                "user_id": "u1",
                "assignment_id": f"a{i}",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "file_url": f"gs://file{i}.pdf",
                "text": f"submission {i}"
            }
            r = await async_client.post("/submissions", json=payload)
            assert r.status_code == 201

        # Get all submissions for user
        r = await async_client.get("/submissions/user/u1")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert all(s["user_id"] == "u1" for s in data)


@pytest.mark.asyncio
async def test_get_nonexistent_submission(async_client):
    """Test getting a submission that doesn't exist."""
    r = await async_client.get("/submissions/nonexistent")
    assert r.status_code == 404


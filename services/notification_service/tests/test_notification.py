"""Tests for Notification Service."""

import pytest
from httpx import AsyncClient, ASGITransport
from services.notification_service.app.main import app
from services.notification_service.app.store import NotificationStore
from services.notification_service.app.client import NotificationServiceClient
from libs.events.schemas import User, Notification
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def notification_store():
    """Create a fresh notification store for each test."""
    return NotificationStore()


@pytest.mark.asyncio
async def test_notify_success():
    """Test creating a notification for an existing user."""
    with patch("services.notification_service.app.main.user_client") as mock_user_client:
        mock_user = User(id="user_123", name="Test", email="test@test.com", role="student")
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {"user_id": "user_123", "message": "Your submission was received"}
            response = await client.post("/notify", json=payload)
            
            assert response.status_code == 201
            data = response.json()
            assert data["user_id"] == "user_123"
            assert data["message"] == "Your submission was received"
            assert "id" in data
            assert "created_at" in data


@pytest.mark.asyncio
async def test_notify_user_not_found():
    """Test notification fails when user doesn't exist."""
    with patch("services.notification_service.app.main.user_client") as mock_client:
        mock_client.get_user = AsyncMock(return_value=None)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {"user_id": "nonexistent", "message": "Test message"}
            response = await client.post("/notify", json=payload)
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_user_notifications():
    """Test retrieving notifications for a specific user."""
    with patch("services.notification_service.app.main.user_client") as mock_user_client:
        mock_user = User(id="user_123", name="Test", email="test@test.com", role="student")
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create multiple notifications
            await client.post("/notify", json={"user_id": "user_123", "message": "Message 1"})
            await client.post("/notify", json={"user_id": "user_123", "message": "Message 2"})
            await client.post("/notify", json={"user_id": "user_456", "message": "Message 3"})
            
            # Get notifications for user_123
            response = await client.get("/notifications/user_123")
            assert response.status_code == 200
            notifications = response.json()
            
            # Filter only the ones we just created in this test
            test_notifications = [n for n in notifications if n["message"] in ["Message 1", "Message 2"]]
            assert len(test_notifications) == 2
            assert all(n["user_id"] == "user_123" for n in test_notifications)
            # Check newest first
            assert test_notifications[0]["message"] == "Message 2"
            assert test_notifications[1]["message"] == "Message 1"


@pytest.mark.asyncio
async def test_list_all_notifications():
    """Test listing all notifications."""
    with patch("services.notification_service.app.main.user_client") as mock_user_client:
        mock_user = User(id="user_123", name="Test", email="test@test.com", role="student")
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create notifications
            await client.post("/notify", json={"user_id": "user_123", "message": "Message 1"})
            await client.post("/notify", json={"user_id": "user_456", "message": "Message 2"})
            
            # Get all notifications
            response = await client.get("/notifications")
            assert response.status_code == 200
            notifications = response.json()
            
            assert len(notifications) >= 2
            # Verify structure
            for n in notifications:
                assert "id" in n
                assert "user_id" in n
                assert "message" in n
                assert "created_at" in n


@pytest.mark.asyncio
async def test_notification_store_add():
    """Test adding notification to store."""
    store = NotificationStore()
    
    notification = await store.add("user_123", "Test message")
    
    assert notification.user_id == "user_123"
    assert notification.message == "Test message"
    assert notification.id is not None
    assert isinstance(notification.created_at, datetime)


@pytest.mark.asyncio
async def test_notification_store_get_by_user():
    """Test getting notifications by user ID."""
    store = NotificationStore()
    
    await store.add("user_123", "Message 1")
    await store.add("user_456", "Message 2")
    await store.add("user_123", "Message 3")
    
    user_notifications = await store.get_by_user("user_123")
    
    assert len(user_notifications) == 2
    assert all(n.user_id == "user_123" for n in user_notifications)
    # Check sorted by newest first
    assert user_notifications[0].message == "Message 3"


@pytest.mark.asyncio
async def test_notification_store_list():
    """Test listing all notifications from store."""
    store = NotificationStore()
    
    await store.add("user_123", "Message 1")
    await store.add("user_456", "Message 2")
    
    all_notifications = await store.list()
    
    assert len(all_notifications) >= 2


@pytest.mark.asyncio
async def test_notification_store_get():
    """Test getting a notification by ID."""
    store = NotificationStore()
    
    created = await store.add("user_123", "Test message")
    retrieved = await store.get(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.user_id == created.user_id
    assert retrieved.message == created.message


@pytest.mark.asyncio
async def test_notification_client_send():
    """Test NotificationServiceClient send method."""
    client = NotificationServiceClient("http://localhost:8005")
    
    # Mock the HTTP client's post method
    with patch.object(client.client, 'post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json = MagicMock(return_value={
            "id": "notif_123",
            "user_id": "user_123",
            "message": "Test notification",
            "created_at": datetime.now().isoformat()
        })
        mock_post.return_value = mock_response
        
        notification = await client.send("user_123", "Test notification")
        
        assert notification is not None
        assert notification.user_id == "user_123"
        assert notification.message == "Test notification"
        
    await client.close()


@pytest.mark.asyncio
async def test_notification_client_get_user_notifications():
    """Test NotificationServiceClient get_user_notifications method."""
    client = NotificationServiceClient("http://localhost:8005")
    
    with patch.object(client.client, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[
            {
                "id": "n1",
                "user_id": "user_123",
                "message": "Message 1",
                "created_at": datetime.now().isoformat()
            }
        ])
        mock_get.return_value = mock_response
        
        notifications = await client.get_user_notifications("user_123")
        
        assert len(notifications) == 1
        assert notifications[0].user_id == "user_123"
        
    await client.close()

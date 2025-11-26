import pytest
from httpx import AsyncClient, ASGITransport
from services.plagiarism_service.app.main import app
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_check():
    """Test plagiarism check endpoint with async client."""
    # Mock user service client, submission service client, and store
    with patch('services.plagiarism_service.app.main.user_service_client') as mock_user_client, \
         patch('services.plagiarism_service.app.main.submission_service_client') as mock_sub_client, \
         patch('services.plagiarism_service.app.main.store') as mock_store:
        
        # Mock user exists
        mock_user = AsyncMock()
        mock_user.id = "u1"
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.role = "student"
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        # Mock store.save
        mock_store.save = AsyncMock(return_value=None)
        
        payload = {
            "id": "s1",
            "user_id": "u1",
            "assignment_id": "a1",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "file_url": "gs://x/y.pdf",
            "text": "hello world"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post("/check", json=payload)
        
        assert res.status_code == 200

        data = res.json()
        assert data["submission_id"] == "s1"
        assert "internal_score" in data
        assert "external_score" in data
        assert "ai_generated_probability" in data
        assert isinstance(data["flagged_sections"], list)
        assert "stub-flag" in data["flagged_sections"]


@pytest.mark.asyncio
async def test_check_user_not_found():
    """Test plagiarism check when user doesn't exist."""
    with patch('services.plagiarism_service.app.main.user_service_client') as mock_user_client:
        # Mock user not found
        mock_user_client.get_user = AsyncMock(return_value=None)
        
        payload = {
            "id": "s1",
            "user_id": "u999",
            "assignment_id": "a1",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "file_url": "gs://x/y.pdf",
            "text": "hello world"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post("/check", json=payload)
        
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_check_missing_text_fetched():
    """Test plagiarism check fetches text from submission service when missing."""
    from libs.events.schemas import Submission
    
    with patch('services.plagiarism_service.app.main.user_service_client') as mock_user_client, \
         patch('services.plagiarism_service.app.main.submission_service_client') as mock_sub_client, \
         patch('services.plagiarism_service.app.main.store') as mock_store:
        
        # Mock user exists
        mock_user = AsyncMock()
        mock_user.id = "u1"
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        # Mock submission service returns submission with text
        full_sub = Submission(
            id="s1",
            user_id="u1",
            assignment_id="a1",
            uploaded_at=datetime.now(timezone.utc),
            file_url="gs://x/y.pdf",
            text="fetched text from submission service"
        )
        mock_sub_client.get = AsyncMock(return_value=full_sub)
        
        # Mock store.save
        mock_store.save = AsyncMock(return_value=None)
        
        payload = {
            "id": "s1",
            "user_id": "u1",
            "assignment_id": "a1",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "file_url": "gs://x/y.pdf",
            "text": None  # Missing text
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post("/check", json=payload)
        
        assert res.status_code == 200
        mock_sub_client.get.assert_called_once_with("s1")

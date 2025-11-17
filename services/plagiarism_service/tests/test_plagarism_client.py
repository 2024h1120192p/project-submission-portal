"""Tests for PlagiarismServiceClient."""
import pytest
from httpx import AsyncClient, ASGITransport
from services.plagiarism_service.app.client import PlagiarismServiceClient
from services.plagiarism_service.app.main import app
from libs.events.schemas import Submission
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_client_check():
    """Test PlagiarismServiceClient check method."""
    with patch('services.plagiarism_service.app.main.user_service_client') as mock_user_client:
        # Mock user exists
        mock_user = AsyncMock()
        mock_user.id = "u1"
        mock_user_client.get_user = AsyncMock(return_value=mock_user)
        
        # Create client pointing to test app
        client = PlagiarismServiceClient("http://test")
        
        # Override the internal httpx client to use the test app
        client._client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        
        submission = Submission(
            id="s1",
            user_id="u1",
            assignment_id="a1",
            uploaded_at=datetime.now(timezone.utc),
            file_url="gs://x/y.pdf",
            text="Test submission text"
        )
        
        result = await client.check(submission)
        
        assert result is not None
        assert result.submission_id == "s1"
        assert 0.0 <= result.internal_score <= 1.0
        assert 0.0 <= result.external_score <= 1.0
        assert 0.0 <= result.ai_generated_probability <= 1.0
        assert "stub-flag" in result.flagged_sections
        
        await client.close()

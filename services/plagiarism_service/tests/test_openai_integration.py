"""Tests for OpenAI AI plagiarism detection integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.plagiarism_service.app.openai_client import OpenAIClient, get_openai_client
from services.plagiarism_service.app.engine import run_plagiarism_pipeline
from libs.events.schemas import Submission
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_openai_client_disabled_by_default():
    """Test that OpenAI client is disabled when no API key is configured."""
    with patch('services.plagiarism_service.app.openai_client.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.OPENAI_MODEL = "gpt-4o-mini"
        mock_settings.OPENAI_ENABLED = False
        
        client = OpenAIClient()
        assert client.enabled is False


@pytest.mark.asyncio
async def test_openai_client_detect_ai_content_disabled():
    """Test AI detection returns default values when disabled."""
    with patch('services.plagiarism_service.app.openai_client.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = ""
        mock_settings.OPENAI_MODEL = "gpt-4o-mini"
        mock_settings.OPENAI_ENABLED = False
        
        client = OpenAIClient()
        result = await client.detect_ai_content("Some test text")
        
        assert result["ai_probability"] == 0.0
        assert result["confidence"] == "low"
        assert result["openai_used"] is False


@pytest.mark.asyncio
async def test_openai_client_detect_ai_content_enabled():
    """Test AI detection calls OpenAI API when enabled."""
    with patch('services.plagiarism_service.app.openai_client.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-4o-mini"
        mock_settings.OPENAI_ENABLED = True
        
        # Mock the openai module import
        with patch.dict('sys.modules', {'openai': MagicMock()}):
            import sys
            mock_openai_module = sys.modules['openai']
            mock_client_instance = AsyncMock()
            mock_openai_module.AsyncOpenAI = MagicMock(return_value=mock_client_instance)
            
            # Mock the chat completion response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"ai_probability": 0.75, "confidence": "high", "indicators": ["repetitive patterns"], "analysis": "High likelihood of AI generation"}'
            mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
            
            # Create a new client (since imports are cached)
            client = OpenAIClient()
            client._client = mock_client_instance
            client.enabled = True
            
            result = await client.detect_ai_content("Some test text that might be AI generated")
            
            assert result["ai_probability"] == 0.75
            assert result["confidence"] == "high"
            assert result["openai_used"] is True
            assert "repetitive patterns" in result["indicators"]


@pytest.mark.asyncio
async def test_plagiarism_pipeline_with_openai_disabled():
    """Test plagiarism pipeline runs without OpenAI when disabled."""
    with patch('services.plagiarism_service.app.engine.get_openai_client') as mock_get_client:
        mock_client = MagicMock()
        mock_client.enabled = False
        mock_get_client.return_value = mock_client
        
        submission = Submission(
            id="test_sub_1",
            user_id="user_1",
            assignment_id="assignment_1",
            uploaded_at=datetime.now(timezone.utc),
            file_url="gs://test/file.pdf",
            text="This is a test research paper text."
        )
        
        result = await run_plagiarism_pipeline(submission)
        
        assert result.submission_id == "test_sub_1"
        assert 0 <= result.internal_score <= 1
        assert 0 <= result.external_score <= 1
        assert 0 <= result.ai_generated_probability <= 1
        assert result.severity in ["low", "medium", "high"]
        assert "stub-flag" in result.flagged_sections


@pytest.mark.asyncio
async def test_plagiarism_pipeline_with_openai_enabled():
    """Test plagiarism pipeline integrates OpenAI detection when enabled."""
    with patch('services.plagiarism_service.app.engine.get_openai_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.enabled = True
        mock_client.detect_ai_content = AsyncMock(return_value={
            "ai_probability": 0.85,
            "confidence": "high",
            "indicators": ["consistent tone", "template phrasing"],
            "analysis": "Likely AI generated",
            "openai_used": True
        })
        mock_get_client.return_value = mock_client
        
        submission = Submission(
            id="test_sub_2",
            user_id="user_1",
            assignment_id="assignment_1",
            uploaded_at=datetime.now(timezone.utc),
            file_url="gs://test/file.pdf",
            text="This is a test research paper text that might be AI generated."
        )
        
        result = await run_plagiarism_pipeline(submission)
        
        assert result.submission_id == "test_sub_2"
        assert result.ai_generated_probability == 0.85
        assert result.ai_generated_likely is True  # >= 0.7 threshold
        assert result.requires_review is True  # Because AI prob >= 0.7
        # Check AI indicators are added to flagged sections
        assert any("ai-indicator:" in f for f in result.flagged_sections)

"""Tests for analytics service."""
import pytest
from httpx import AsyncClient, ASGITransport
from services.analytics_service.app.main import app
from services.analytics_service.app.store import add_window, ANALYTICS_DB
from services.analytics_service.app.client import AnalyticsServiceClient
from datetime import datetime, timezone
from libs.events.schemas import AnalyticsWindow


@pytest.mark.asyncio
async def test_latest_and_history():
    """Test latest and history endpoints."""
    # Clear DB for test
    ANALYTICS_DB.clear()
    
    # Add test window
    await add_window(
        AnalyticsWindow(
            timestamp=datetime.now(timezone.utc),
            submission_rate=12.0,
            avg_plagiarism=0.33,
            avg_ai_probability=0.21,
            spike_detected=False,
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        r_latest = await client.get("/analytics/latest")
        assert r_latest.status_code == 200
        data = r_latest.json()
        assert data["submission_rate"] == 12.0

        r_hist = await client.get("/analytics/history")
        assert r_hist.status_code == 200
        assert len(r_hist.json()) >= 1


@pytest.mark.asyncio
async def test_no_analytics_yet():
    """Test 404 when no analytics data exists."""
    ANALYTICS_DB.clear()
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        r = await client.get("/analytics/latest")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_analytics_client():
    """Test AnalyticsServiceClient."""
    ANALYTICS_DB.clear()
    
    # Add test data
    await add_window(
        AnalyticsWindow(
            timestamp=datetime.now(timezone.utc),
            submission_rate=5.0,
            avg_plagiarism=0.15,
            avg_ai_probability=0.12,
            spike_detected=False,
        )
    )
    
    # Test client
    client = AnalyticsServiceClient("http://test")
    client._client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    )
    
    latest = await client.get_latest()
    assert latest is not None
    assert latest.submission_rate == 5.0
    
    history = await client.get_history()
    assert len(history) == 1
    
    await client.close()


@pytest.mark.asyncio
async def test_compute_analytics():
    """Test compute analytics endpoint (stub implementation)."""
    ANALYTICS_DB.clear()
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        r = await client.post("/analytics/compute")
        assert r.status_code == 200
        data = r.json()
        assert "timestamp" in data
        assert "submission_rate" in data
        assert "avg_plagiarism" in data
        assert "avg_ai_probability" in data
        assert "spike_detected" in data


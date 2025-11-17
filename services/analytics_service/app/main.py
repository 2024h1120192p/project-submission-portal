"""Analytics service main application.

Provides windowed analytics data including submission rates,
plagiarism averages, and AI probability metrics.
"""
from fastapi import FastAPI, HTTPException
from libs.events.schemas import AnalyticsWindow
from .store import get_latest, get_history, add_window
from config.settings import get_settings
import httpx
from datetime import datetime, timezone

app = FastAPI(title="Analytics Service")
settings = get_settings()


@app.get("/analytics/latest", response_model=AnalyticsWindow)
async def latest():
    """Get the latest analytics window.
    
    Returns:
        AnalyticsWindow: The most recent analytics window
        
    Raises:
        HTTPException: 404 if no analytics data exists
    """
    w = await get_latest()
    if not w:
        raise HTTPException(status_code=404, detail="No analytics yet")
    return w


@app.get("/analytics/history", response_model=list[AnalyticsWindow])
async def history():
    """Get all historical analytics windows.
    
    Returns:
        List[AnalyticsWindow]: All analytics windows ordered by timestamp
    """
    return await get_history()


@app.post("/analytics/compute")
async def compute_analytics():
    """Compute current analytics window from submission and plagiarism services.
    
    This is a stub implementation that fetches data from other services
    and computes windowed analytics.
    
    Returns:
        AnalyticsWindow: The newly computed analytics window
    """
    # Fetch data from other services (stub implementation)
    submission_count = await _get_submission_count()
    plagiarism_avg = await _get_plagiarism_average()
    
    # Create analytics window
    window = AnalyticsWindow(
        timestamp=datetime.now(timezone.utc),
        submission_rate=submission_count / 60.0,  # per minute
        avg_plagiarism=plagiarism_avg,
        avg_ai_probability=plagiarism_avg * 0.8,  # stub calculation
        spike_detected=submission_count > 10  # simple threshold
    )
    
    await add_window(window)
    return window


async def _get_submission_count() -> int:
    """Fetch submission count from submission service (stub).
    
    Returns:
        int: Number of recent submissions
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.SUBMISSION_SERVICE_URL}/submissions/count",
                timeout=5.0
            )
            if resp.status_code == 200:
                return resp.json().get("count", 0)
    except Exception as e:
        print(f"Error fetching submission count: {e}")
    return 0


async def _get_plagiarism_average() -> float:
    """Fetch average plagiarism score from plagiarism service (stub).
    
    Returns:
        float: Average plagiarism score (0.0 to 1.0)
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.PLAGIARISM_SERVICE_URL}/stats/average",
                timeout=5.0
            )
            if resp.status_code == 200:
                return resp.json().get("average", 0.0)
    except Exception as e:
        print(f"Error fetching plagiarism average: {e}")
    return 0.0

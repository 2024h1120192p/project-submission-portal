"""Analytics service main application.

Provides windowed analytics data including submission rates,
plagiarism averages, and AI probability metrics.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from libs.events.schemas import AnalyticsWindow
from libs.events import KafkaConsumerClient
from config.logging import get_logger
from .store import get_latest, get_history, add_window
from config.settings import get_settings
import asyncio
from datetime import datetime, timezone

logger = get_logger(__name__)
settings = get_settings()

# Initialize Kafka client
kafka_broker = getattr(settings, 'KAFKA_BROKER', 'kafka:29092')
kafka_client = KafkaConsumerClient(
    broker=kafka_broker,
    group_id="analytics-service",
    topics=["paper_uploaded", "plagiarism_checked"]
)

# Analytics state
analytics_state = {
    'submission_count': 0,
    'plagiarism_scores': [],
    'consumer_task': None,
}


async def handle_plagiarism_event(event: dict):
    """Handle plagiarism_checked events from Kafka."""
    try:
        score = event.get('internal_score', 0.0)
        analytics_state['plagiarism_scores'].append(score)
        # Keep only last 100 scores for efficiency
        if len(analytics_state['plagiarism_scores']) > 100:
            analytics_state['plagiarism_scores'].pop(0)
        logger.info(f"Plagiarism event processed, current avg: {sum(analytics_state['plagiarism_scores']) / len(analytics_state['plagiarism_scores']):.2f}")
    except Exception as e:
        logger.error(f"Error handling plagiarism event: {e}")


async def handle_submission_event(event: dict):
    """Handle paper_uploaded events from Kafka."""
    try:
        analytics_state['submission_count'] += 1
        logger.info(f"Submission event processed, total count: {analytics_state['submission_count']}")
    except Exception as e:
        logger.error(f"Error handling submission event: {e}")


async def start_kafka_consumer():
    """Start consuming events from Kafka."""
    kafka_client.register_handler("paper_uploaded", handle_submission_event)
    kafka_client.register_handler("plagiarism_checked", handle_plagiarism_event)
    
    await kafka_client.start()
    await kafka_client.consume()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    task = asyncio.create_task(start_kafka_consumer())
    analytics_state['consumer_task'] = task
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    task.cancel()
    try:
        await kafka_client.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(title="Analytics Service", lifespan=lifespan)


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
    """Compute current analytics window from Kafka events.
    
    Uses data collected from Kafka consumers to compute analytics.
    
    Returns:
        AnalyticsWindow: The newly computed analytics window
    """
    # Use data collected from Kafka events
    submission_count = analytics_state['submission_count']
    plagiarism_scores = analytics_state['plagiarism_scores']
    
    plagiarism_avg = (sum(plagiarism_scores) / len(plagiarism_scores)) if plagiarism_scores else 0.0
    
    # Create analytics window
    window = AnalyticsWindow(
        timestamp=datetime.now(timezone.utc),
        submission_rate=submission_count / 60.0,  # per minute
        avg_plagiarism=plagiarism_avg,
        avg_ai_probability=plagiarism_avg * 0.8,  # based on plagiarism score
        spike_detected=submission_count > 10  # simple threshold
    )
    
    await add_window(window)
    logger.info(f"Analytics computed: {submission_count} submissions, avg plagiarism: {plagiarism_avg:.2f}")
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

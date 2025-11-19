"""Analytics service main application.

Provides windowed analytics data including submission rates,
plagiarism averages, and AI probability metrics.

Uses embedded Flink for windowed aggregations instead of separate Kafka consumer.
"""
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from libs.events.schemas import AnalyticsWindow
from libs.events import KafkaConsumerClient
from config.logging import get_logger
from .store import get_latest, get_history, add_window
from .stream_processor import create_stream_processor
from config.settings import get_settings
import asyncio
import httpx
from datetime import datetime, timezone

logger = get_logger(__name__)
settings = get_settings()

# Initialize Kafka client for consuming aggregated windows
kafka_broker = getattr(settings, 'KAFKA_BROKER', 'kafka:29092')
kafka_client = KafkaConsumerClient(
    broker=kafka_broker,
    group_id="analytics-service",
    topics=["analytics_window"]  # Consume Flink-aggregated analytics topic
)

# Initialize Flink stream processor for windowed aggregations
stream_processor = create_stream_processor(kafka_broker=kafka_broker, window_minutes=5)

# Analytics state
analytics_state = {
    'latest_window': None,
    'windows_history': [],
    'consumer_task': None,
}


async def handle_analytics_window(event: dict):
    """Handle pre-aggregated analytics windows from embedded Flink processor.
    
    Flink (embedded in this service) performs windowed aggregations
    and publishes to analytics_window topic, which we consume here.
    """
    try:
        # Store the latest window data from Flink
        analytics_state['latest_window'] = event
        
        # Keep history (last 100 windows)
        analytics_state['windows_history'].append(event)
        if len(analytics_state['windows_history']) > 100:
            analytics_state['windows_history'].pop(0)
        
        logger.info(
            f"Analytics window received: "
            f"submissions={event.get('submission_count', 0)}, "
            f"avg_internal={event.get('avg_internal_score', 0):.2f}, "
            f"high_risk={event.get('high_risk_count', 0)}"
        )
        
        # Store in Redis for API queries
        window_data = AnalyticsWindow(
            window_start=event.get('window_start', datetime.now(timezone.utc).isoformat()),
            window_end=datetime.now(timezone.utc).isoformat(),
            submission_count=event.get('submission_count', 0),
            avg_internal_score=event.get('avg_internal_score', 0.0),
            avg_external_score=event.get('avg_external_score', 0.0),
            avg_ai_probability=event.get('avg_ai_probability', 0.0),
            high_risk_count=event.get('high_risk_count', 0),
            total_checks=event.get('total_checks', 0)
        )
        await add_window(window_data)
        
    except Exception as e:
        logger.error(f"Error handling analytics window: {e}")


async def start_kafka_consumer():
    """Start consuming pre-aggregated analytics windows from Flink."""
    kafka_client.register_handler("analytics_window", handle_analytics_window)
    
    await kafka_client.start()
    await kafka_client.consume()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    try:
        # Start Flink stream processor for windowed aggregations
        await stream_processor.start()
        
        # Start Kafka consumer to receive aggregated windows
        task = asyncio.create_task(start_kafka_consumer())
        analytics_state['consumer_task'] = task
        
        logger.info("Application started successfully with embedded Flink stream processor")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
    
    yield
    
    # Shutdown
    try:
        if analytics_state['consumer_task']:
            analytics_state['consumer_task'].cancel()
        
        await stream_processor.stop()
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

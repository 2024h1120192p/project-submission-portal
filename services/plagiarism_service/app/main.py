from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
from libs.events.schemas import Submission, PlagiarismResult
from libs.events import KafkaProducerClient
from config.logging import get_logger
from .engine import run_plagiarism_pipeline
from .store import store
from .stream_processor import create_stream_processor
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Initialize clients
user_service_client = UserServiceClient(settings.USERS_SERVICE_URL)
submission_service_client = SubmissionServiceClient(settings.SUBMISSION_SERVICE_URL)
# Use configured Kafka broker from settings
kafka_broker = settings.KAFKA_BROKER
kafka_client = KafkaProducerClient(broker=kafka_broker)

# Initialize Flink stream processor
stream_processor = create_stream_processor(kafka_broker=kafka_broker)

# Track Kafka availability
kafka_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global kafka_available
    # Startup
    try:
        kafka_available = await kafka_client.start(skip_on_error=True)
        if kafka_available:
            logger.info("Kafka producer started successfully")
        else:
            logger.warning("Kafka producer unavailable - running in fallback mode")
        
        # Start Flink stream processor for consuming and processing events (also graceful)
        try:
            await stream_processor.start()
            logger.info("Stream processor started successfully")
        except Exception as e:
            logger.warning(f"Stream processor failed to start: {e} - continuing without it")
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
    
    yield
    
    # Shutdown
    try:
        await stream_processor.stop()
        await kafka_client.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(lifespan=lifespan)


@app.post("/check", response_model=PlagiarismResult)
async def check(sub: Submission):
    """Check research paper submission for plagiarism.
    
    If submission text is missing, fetches it from submission-service.
    Also validates user exists via user-service.
    Stores results in MongoDB.
    """
    # Validate user exists
    user = await user_service_client.get_user(sub.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {sub.user_id} not found"
        )
    
    # Fetch submission text if missing
    if not sub.text:
        full_submission = await submission_service_client.get(sub.id)
        if full_submission and full_submission.text:
            sub.text = full_submission.text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Research paper text is required for plagiarism check"
            )
    
    # Run plagiarism check
    result = await run_plagiarism_pipeline(sub)
    
    # Save result to MongoDB
    await store.save(result)
    
    # Emit Kafka event
    try:
        await kafka_client.emit("plagiarism_checked", result.model_dump())
    except Exception as e:
        logger.error(f"Failed to emit event: {e}")
    
    return result


@app.get("/results/{submission_id}", response_model=PlagiarismResult)
async def get_result(submission_id: str):
    """Get plagiarism result for a research paper submission."""
    result = await store.get(submission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No plagiarism result found for submission {submission_id}"
        )
    return result


@app.get("/stats")
async def get_stats():
    """Get plagiarism statistics."""
    return await store.get_statistics()

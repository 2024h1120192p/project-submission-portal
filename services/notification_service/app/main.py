from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .store import store
from libs.events.schemas import Notification
from libs.events import KafkaConsumerClient
from config.logging import get_logger
from services.users_service.app.client import UserServiceClient
from config.settings import get_settings
from typing import List
import asyncio

logger = get_logger(__name__)
settings = get_settings()

# Initialize clients
user_client = UserServiceClient(settings.USERS_SERVICE_URL)
kafka_broker = getattr(settings, 'KAFKA_BROKER', 'localhost:9092')
kafka_client = KafkaConsumerClient(
    broker=kafka_broker,
    group_id="notification-service",
    topics=["paper_uploaded_processed", "plagiarism_checked_processed"]  # Use Flink-processed topics
)

# Notification state
notification_state = {
    'consumer_task': None,
}


async def handle_plagiarism_event(event: dict):
    """Handle plagiarism_checked events and create notifications.
    
    Now receives enriched events from Flink with severity and metadata.
    """
    try:
        submission_id = event.get('submission_id')
        user_id = event.get('user_id')
        internal_score = event.get('internal_score', 0.0)
        severity = event.get('severity', 'unknown')
        requires_review = event.get('requires_review', False)
        
        # Create notification based on severity
        if severity == 'high':
            message = f"⚠️ HIGH RISK: Plagiarism check for submission {submission_id} detected {internal_score:.1%} similarity. Manual review required."
        elif requires_review:
            message = f"⚠️ REVIEW NEEDED: Plagiarism check for submission {submission_id} detected {internal_score:.1%} similarity."
        else:
            message = f"✓ Plagiarism check completed for submission {submission_id}: {internal_score:.1%} similarity ({severity} risk)"
        
        # Validate user exists
        user = await user_client.get_user(user_id)
        if user:
            await store.add(user_id, message)
            logger.info(f"Notification created for user {user_id} (severity: {severity})")
        else:
            logger.warning(f"User {user_id} not found, skipping notification")
    except Exception as e:
        logger.error(f"Error handling plagiarism event: {e}")


async def handle_submission_event(event: dict):
    """Handle paper_uploaded events and create notifications.
    
    Now receives enriched events from Flink with processing metadata.
    """
    try:
        submission_id = event.get('id')
        user_id = event.get('user_id')
        text_length = event.get('text_length', 0)
        
        message = f"✓ Your paper (submission {submission_id}, {text_length} characters) has been successfully uploaded and is queued for plagiarism checking"
        
        # Validate user exists
        user = await user_client.get_user(user_id)
        if user:
            await store.add(user_id, message)
            logger.info(f"Notification created for user {user_id}")
        else:
            logger.warning(f"User {user_id} not found, skipping notification")
    except Exception as e:
        logger.error(f"Error handling submission event: {e}")


async def start_kafka_consumer():
    """Start consuming events from Kafka (Flink-processed topics)."""
    kafka_client.register_handler("paper_uploaded_processed", handle_submission_event)
    kafka_client.register_handler("plagiarism_checked_processed", handle_plagiarism_event)
    
    await kafka_client.start()
    await kafka_client.consume()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    task = asyncio.create_task(start_kafka_consumer())
    notification_state['consumer_task'] = task
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    task.cancel()
    try:
        await kafka_client.close()
        await user_client.client.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


app = FastAPI(title="Notification Service", lifespan=lifespan)


class NotifyRequest(BaseModel):
    user_id: str
    message: str


@app.post("/notify", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def notify(req: NotifyRequest):
    """Create a notification for a user.
    
    Args:
        req: NotifyRequest with user_id and message
        
    Returns:
        Notification: Created notification object
        
    Raises:
        HTTPException: 404 if user does not exist
    """
    # Validate user exists
    user = await user_client.get_user(req.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {req.user_id} not found"
        )
    
    # Create notification
    notification = await store.add(req.user_id, req.message)
    return notification


@app.get("/notifications/{user_id}", response_model=List[Notification])
async def get_user_notifications(user_id: str):
    """Get all notifications for a specific user.
    
    Args:
        user_id: User ID to fetch notifications for
        
    Returns:
        List[Notification]: List of notifications for the user
    """
    notifications = await store.get_by_user(user_id)
    return notifications


@app.get("/notifications", response_model=List[Notification])
async def list_all_notifications():
    """Get all notifications.
    
    Returns:
        List[Notification]: All notifications in the system
    """
    return await store.list()

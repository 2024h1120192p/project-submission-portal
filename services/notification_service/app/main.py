from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from .store import store
from libs.events.schemas import Notification
from services.users_service.app.client import UserServiceClient
from config.settings import get_settings
from typing import List
import asyncio

app = FastAPI(title="Notification Service")
settings = get_settings()

# User service client for validation
user_client = UserServiceClient(settings.USERS_SERVICE_URL)

# Kafka consumer stub (for future implementation)
class KafkaConsumerStub:
    """Stub for future Kafka subscription implementation."""
    
    async def start(self):
        """Start consuming messages from Kafka topics."""
        # TODO: Implement Kafka consumer
        # - Subscribe to relevant topics (e.g., plagiarism_checked)
        # - Process events and create notifications
        pass
    
    async def stop(self):
        """Stop Kafka consumer gracefully."""
        # TODO: Implement graceful shutdown
        pass

kafka_consumer = KafkaConsumerStub()


class NotifyRequest(BaseModel):
    user_id: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    # Future: Start Kafka consumer
    # await kafka_consumer.start()
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # Future: Stop Kafka consumer
    # await kafka_consumer.stop()
    await user_client.client.close()


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

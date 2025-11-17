from fastapi import FastAPI, HTTPException, status
from libs.events.schemas import Submission
from libs.events.kafka import emit_event
from .store import SubmissionStore
from services.user_service.app.client import UserServiceClient
from config.settings import get_settings
from datetime import datetime, timezone
import uuid
from typing import List

app = FastAPI()
store = SubmissionStore()
settings = get_settings()

# Initialize user service client
user_service_client = UserServiceClient(settings.USER_SERVICE_URL)


@app.post("/submissions", response_model=Submission, status_code=status.HTTP_201_CREATED)
async def create_submission(sub: Submission):
    """Create a new submission after validating user exists."""
    # Validate user exists
    user = await user_service_client.get_user(sub.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {sub.user_id} not found"
        )
    
    # Create submission
    new_sub = Submission(
        id=sub.id or str(uuid.uuid4()),
        user_id=sub.user_id,
        assignment_id=sub.assignment_id,
        uploaded_at=sub.uploaded_at or datetime.now(timezone.utc),
        file_url=sub.file_url,
        text=sub.text,
    )
    
    await store.save(new_sub)
    
    # Emit Kafka event
    emit_event("submission_uploaded", new_sub.model_dump(mode='json'))
    
    return new_sub


@app.get("/submissions/{submission_id}", response_model=Submission)
async def get_submission(submission_id: str):
    """Get a submission by ID."""
    submission = await store.get(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    return submission


@app.get("/submissions/user/{user_id}", response_model=List[Submission])
async def get_by_user(user_id: str):
    """Get all submissions for a specific user."""
    return await store.get_by_user(user_id)

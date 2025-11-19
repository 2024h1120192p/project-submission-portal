from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from libs.events.schemas import Submission
from libs.events.kafka import emit_event
from .store import SubmissionStore
from services.users_service.app.client import UserServiceClient
from config.settings import get_settings
from datetime import datetime, timezone
from pathlib import Path
import uuid
import aiofiles
from typing import List

app = FastAPI()
store = SubmissionStore()
settings = get_settings()

# Initialize user service client
user_service_client = UserServiceClient(settings.USERS_SERVICE_URL)

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/submissions", response_model=Submission, status_code=status.HTTP_201_CREATED)
async def create_submission(sub: Submission):
    """Create a new research paper submission after validating user exists."""
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
    emit_event("paper_uploaded", new_sub.model_dump(mode='json'))
    
    return new_sub


@app.get("/submissions/{submission_id}", response_model=Submission)
async def get_submission(submission_id: str):
    """Get a research paper submission by ID."""
    submission = await store.get(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission {submission_id} not found"
        )
    return submission


@app.post("/submissions/user/{user_id}", response_model=List[Submission])
async def get_by_user(user_id: str):
    """Get all research paper submissions for a specific user."""
    return await store.get_by_user(user_id)


@app.post("/submissions/upload", response_model=Submission, status_code=status.HTTP_201_CREATED)
async def upload_file(
    user_id: str = Form(...),
    assignment_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a research paper file and create submission record.
    
    Handles file storage and creates submission entry.
    """
    # Validate user exists
    user = await user_service_client.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Extract text content if it's a text file
    text_content = None
    if file_ext.lower() in ['.txt', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.md']:
        try:
            text_content = content.decode('utf-8')
        except:
            text_content = None
    
    # Create submission record
    new_sub = Submission(
        id=str(uuid.uuid4()),
        user_id=user_id,
        assignment_id=assignment_id,
        uploaded_at=datetime.now(timezone.utc),
        file_url=f"/uploads/{unique_filename}",
        text=text_content,
    )
    
    await store.save(new_sub)
    
    # Emit Kafka event
    emit_event("paper_uploaded", new_sub.model_dump(mode='json'))
    
    return new_sub

"""API routes for research paper submission uploads and management."""
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uuid
import aiofiles
import os
from datetime import datetime, timezone
from libs.events.schemas import Submission

router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory="services/gateway/app/templates")


@router.post("/submissions/upload")
async def upload_submission(
    request: Request,
    assignment_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload research paper submission.
    
    Researchers can upload their paper files here.
    The file is saved locally and a submission record is created.
    """
    clients = request.state.clients
    
    # TODO: Get user_id from authentication/session
    # For now, using demo user
    user_id = "student_001"
    
    # Validate user exists
    user = await clients.user.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only researchers can upload paper submissions"
        )
    
    # Validate file
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Read text content if it's a text file
    text_content = None
    if file_ext.lower() in ['.txt', '.py', '.java', '.cpp', '.c', '.js', '.html', '.css']:
        try:
            text_content = content.decode('utf-8')
        except:
            text_content = None
    
    # Create submission record
    submission = Submission(
        id=str(uuid.uuid4()),
        user_id=user_id,
        assignment_id=assignment_id,
        uploaded_at=datetime.now(timezone.utc),
        file_url=f"/uploads/{unique_filename}",
        text=text_content
    )
    
    # Save to submission service
    created_submission = await clients.submission.create(submission)
    
    if not created_submission:
        # Cleanup file if submission creation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission record"
        )
    
    # Trigger plagiarism check if text content is available
    if text_content:
        try:
            plagiarism_result = await clients.plagiarism.check(created_submission)
        except Exception as e:
            # Continue even if plagiarism check fails
            pass
    
    # Return HTML success page with auto-redirect using template
    return templates.TemplateResponse(
        "submission_success.html",
        {
            "request": request,
            "paper_id": assignment_id
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/submissions")
async def list_submissions(request: Request, user_id: str = None):
    """List paper submissions. If user_id provided, filter by user."""
    clients = request.state.clients
    
    if user_id:
        submissions = await clients.submission.list_by_user(user_id)
    else:
        # TODO: Implement list all for admin/faculty
        submissions = []
    
    return [sub.model_dump(mode='json') for sub in submissions]


@router.get("/submissions/{submission_id}")
async def get_submission(request: Request, submission_id: str):
    """Get research paper submission details."""
    clients = request.state.clients
    
    submission = await clients.submission.get(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper submission not found"
        )
    
    return submission.model_dump(mode='json')

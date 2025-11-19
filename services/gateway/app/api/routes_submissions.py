"""API routes for research paper submission uploads and management.

Gateway only orchestrates - validation and business logic delegated to client and services.
"""
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory="services/gateway/app/templates")


@router.post("/submissions/upload")
async def upload_submission(
    request: Request,
    assignment_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload research paper submission - orchestrate through client.
    
    Researchers can upload their paper files here.
    Delegates file handling to the submission service.
    """
    clients = request.state.clients
    
    # TODO: Get user_id from authentication/session
    # For now, using demo user
    user_id = "student_001"
    
    # Orchestrate user validation through client
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
    
    # Basic validation
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Read file content
    content = await file.read()
    
    # Basic size check
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Orchestrate upload through client (handles plagiarism check too)
    created_submission = await clients.handle_submission_upload(
        user_id=user_id,
        assignment_id=assignment_id,
        file_content=content,
        filename=file.filename
    )
    
    if not created_submission:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create submission record"
        )
    
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
    """List paper submissions - orchestrate through client."""
    clients = request.state.clients
    
    if user_id:
        submissions = await clients.get_user_submissions(user_id)
    else:
        # TODO: Implement list all for admin/faculty
        submissions = []
    
    return [sub.model_dump(mode='json') for sub in submissions]


@router.get("/submissions/{submission_id}")
async def get_submission(request: Request, submission_id: str):
    """Get research paper submission details - orchestrate through client."""
    clients = request.state.clients
    
    submission = await clients.get_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper submission not found"
        )
    
    return submission.model_dump(mode='json')

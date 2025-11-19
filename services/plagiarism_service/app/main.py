from fastapi import FastAPI, HTTPException, status
from libs.events.schemas import Submission, PlagiarismResult
from libs.events.kafka import emit_event
from .engine import run_plagiarism_pipeline
from .store import store
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from config.settings import get_settings

app = FastAPI()
settings = get_settings()

# Initialize service clients
user_service_client = UserServiceClient(settings.USERS_SERVICE_URL)
submission_service_client = SubmissionServiceClient(settings.SUBMISSION_SERVICE_URL)


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
    emit_event("plagiarism_checked", result.model_dump())
    
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

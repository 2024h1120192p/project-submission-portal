from fastapi import FastAPI, HTTPException, status
from libs.events.schemas import Submission, PlagiarismResult
from libs.events.kafka import emit_event
from .engine import run_plagiarism_pipeline
from services.user_service.app.client import UserServiceClient
from config.settings import get_settings
import httpx

app = FastAPI()
settings = get_settings()

# Initialize service clients
user_service_client = UserServiceClient(settings.USER_SERVICE_URL)


class SubmissionServiceClient:
    """Client for fetching submissions from submission-service."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)
    
    async def get_submission(self, submission_id: str) -> Submission | None:
        """Fetch a submission by ID."""
        try:
            resp = await self._client.get(f"/submissions/{submission_id}")
            if resp.status_code == 200:
                return Submission(**resp.json())
            return None
        except Exception:
            return None
    
    async def close(self):
        await self._client.aclose()


submission_service_client = SubmissionServiceClient(settings.SUBMISSION_SERVICE_URL)


@app.post("/check", response_model=PlagiarismResult)
async def check(sub: Submission):
    """Check submission for plagiarism.
    
    If submission text is missing, fetches it from submission-service.
    Also validates user exists via user-service.
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
        full_submission = await submission_service_client.get_submission(sub.id)
        if full_submission and full_submission.text:
            sub.text = full_submission.text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission text is required for plagiarism check"
            )
    
    # Run plagiarism check
    result = await run_plagiarism_pipeline(sub)
    
    # Emit Kafka event
    emit_event("plagiarism_checked", result.model_dump())
    
    return result

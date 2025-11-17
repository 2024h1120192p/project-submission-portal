"""Client for plagiarism service."""
import httpx
from libs.events.schemas import Submission, PlagiarismResult
from typing import Optional


class PlagiarismServiceClient:
    """Async client for plagiarism service.
    
    Provides methods to interact with the plagiarism service API.
    Uses httpx.AsyncClient for async HTTP requests.
    """
    
    def __init__(self, base_url: str):
        """Initialize client with base URL.
        
        Args:
            base_url: Base URL of the plagiarism service (e.g., http://localhost:8003)
        """
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)
    
    async def check(self, submission: Submission) -> Optional[PlagiarismResult]:
        """Check a submission for plagiarism.
        
        Args:
            submission: Submission object to check
            
        Returns:
            PlagiarismResult if successful, None otherwise
        """
        try:
            resp = await self._client.post(
                "/check",
                json=submission.model_dump(mode='json')
            )
            if resp.status_code == 200:
                return PlagiarismResult(**resp.json())
            return None
        except Exception as e:
            print(f"Error checking plagiarism: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

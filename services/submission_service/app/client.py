"""Client for interacting with the submission service from other services."""
import httpx
from libs.events.schemas import Submission
from typing import List, Optional


class SubmissionServiceClient:
    """Async client for submission service operations."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def get(self, submission_id: str) -> Optional[Submission]:
        """Get a submission by ID.
        
        Args:
            submission_id: The submission ID to retrieve
            
        Returns:
            Submission object if found, None otherwise
        """
        try:
            resp = await self._client.get(f"/submissions/{submission_id}")
            if resp.status_code == 200:
                return Submission(**resp.json())
        except Exception:
            pass
        return None

    async def list_by_user(self, user_id: str) -> List[Submission]:
        """Get all submissions for a specific user.
        
        Args:
            user_id: The user ID to filter submissions by
            
        Returns:
            List of Submission objects
        """
        try:
            resp = await self._client.get(f"/submissions/user/{user_id}")
            if resp.status_code == 200:
                return [Submission(**s) for s in resp.json()]
        except Exception:
            pass
        return []

    async def create(self, submission: Submission) -> Optional[Submission]:
        """Create a new submission.
        
        Args:
            submission: The Submission object to create
            
        Returns:
            Created Submission object if successful, None otherwise
        """
        try:
            resp = await self._client.post(
                "/submissions",
                json=submission.model_dump(mode='json')
            )
            if resp.status_code in (200, 201):
                return Submission(**resp.json())
        except Exception:
            pass
        return None

    async def upload_file(
        self,
        user_id: str,
        assignment_id: str,
        file_content: bytes,
        filename: str
    ) -> Optional[Submission]:
        """Upload a file and create submission.
        
        Args:
            user_id: The user uploading the file
            assignment_id: The assignment/paper ID
            file_content: The file content as bytes
            filename: Original filename
            
        Returns:
            Created Submission object if successful, None otherwise
        """
        try:
            files = {"file": (filename, file_content)}
            data = {
                "user_id": user_id,
                "assignment_id": assignment_id
            }
            resp = await self._client.post(
                "/submissions/upload",
                files=files,
                data=data
            )
            if resp.status_code in (200, 201):
                return Submission(**resp.json())
        except Exception:
            pass
        return None

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

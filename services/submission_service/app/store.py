from libs.events.schemas import Submission
from typing import Optional, List


class SubmissionStore:
    """Async in-memory store for submissions."""
    
    def __init__(self):
        self.db: dict[str, Submission] = {}

    async def save(self, sub: Submission) -> Submission:
        """Save a submission to the store."""
        self.db[sub.id] = sub
        return sub

    async def get(self, sub_id: str) -> Optional[Submission]:
        """Get a submission by ID."""
        return self.db.get(sub_id)

    async def get_by_user(self, user_id: str) -> List[Submission]:
        """Get all submissions for a specific user."""
        return [s for s in self.db.values() if s.user_id == user_id]
    
    async def get_all(self) -> List[Submission]:
        """Get all submissions."""
        return list(self.db.values())

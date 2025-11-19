"""Plagiarism results store with MongoDB backend using Motor async."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from libs.events.schemas import PlagiarismResult
from config.settings import get_settings

settings = get_settings()


class PlagiarismStore:
    """Async MongoDB-backed plagiarism results store."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._initialized = False

    async def initialize(self):
        """Initialize MongoDB connection."""
        if not self._initialized:
            self.client = AsyncIOMotorClient(settings.MONGO_URL)
            self.db = self.client[settings.MONGO_DB]
            self.collection = self.db["plagiarism_results"]
            # Create index on submission_id for faster lookups
            await self.collection.create_index("submission_id", unique=True)
            self._initialized = True

    async def save(self, result: PlagiarismResult) -> PlagiarismResult:
        """Save plagiarism result to MongoDB."""
        await self.initialize()
        doc = {
            "submission_id": result.submission_id,
            "internal_score": result.internal_score,
            "external_score": result.external_score,
            "ai_generated_probability": result.ai_generated_probability,
            "flagged_sections": result.flagged_sections
        }
        # Use replace_one with upsert to replace existing or insert new
        await self.collection.replace_one(
            {"submission_id": result.submission_id},
            doc,
            upsert=True
        )
        return result

    async def get(self, submission_id: str) -> Optional[PlagiarismResult]:
        """Get plagiarism result by submission ID."""
        await self.initialize()
        doc = await self.collection.find_one({"submission_id": submission_id})
        if doc:
            return PlagiarismResult(
                submission_id=doc["submission_id"],
                internal_score=doc["internal_score"],
                external_score=doc["external_score"],
                ai_generated_probability=doc["ai_generated_probability"],
                flagged_sections=doc["flagged_sections"]
            )
        return None

    async def get_all(self) -> List[PlagiarismResult]:
        """Get all plagiarism results."""
        await self.initialize()
        cursor = self.collection.find()
        results = []
        async for doc in cursor:
            results.append(
                PlagiarismResult(
                    submission_id=doc["submission_id"],
                    internal_score=doc["internal_score"],
                    external_score=doc["external_score"],
                    ai_generated_probability=doc["ai_generated_probability"],
                    flagged_sections=doc["flagged_sections"]
                )
            )
        return results

    async def get_statistics(self) -> dict:
        """Get aggregated statistics from plagiarism results."""
        await self.initialize()
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_internal": {"$avg": "$internal_score"},
                    "avg_external": {"$avg": "$external_score"},
                    "avg_ai": {"$avg": "$ai_generated_probability"},
                    "count": {"$sum": 1}
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        async for doc in cursor:
            return {
                "average_internal_score": doc.get("avg_internal", 0.0),
                "average_external_score": doc.get("avg_external", 0.0),
                "average_ai_probability": doc.get("avg_ai", 0.0),
                "total_checks": doc.get("count", 0)
            }
        return {
            "average_internal_score": 0.0,
            "average_external_score": 0.0,
            "average_ai_probability": 0.0,
            "total_checks": 0
        }


store = PlagiarismStore()

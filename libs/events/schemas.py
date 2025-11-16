# libs/events/schemas.py
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class User(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["student", "faculty"]

class Submission(BaseModel):
    id: str
    user_id: str
    assignment_id: str
    uploaded_at: datetime
    file_url: str
    text: str | None = None

class PlagiarismResult(BaseModel):
    submission_id: str
    internal_score: float
    external_score: float
    ai_generated_probability: float
    flagged_sections: list[str]

class AnalyticsWindow(BaseModel):
    timestamp: datetime
    submission_rate: float
    avg_plagiarism: float
    avg_ai_probability: float
    spike_detected: bool

class Notification(BaseModel):
    id: str
    user_id: str
    message: str
    created_at: datetime
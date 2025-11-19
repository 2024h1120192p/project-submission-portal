"""Event schema definitions using Pydantic models.

All models are async-compatible and can be used in async contexts.
"""
from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime
import json


class User(BaseModel):
    """User model for event payloads."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    email: str
    role: Literal["student", "faculty"]


class Submission(BaseModel):
    """Research paper submission model for event payloads."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    assignment_id: str
    uploaded_at: datetime
    file_url: str
    text: str | None = None


class PlagiarismResult(BaseModel):
    """Plagiarism detection result for research papers."""
    
    model_config = ConfigDict(from_attributes=True)
    
    submission_id: str
    internal_score: float
    external_score: float
    ai_generated_probability: float
    flagged_sections: list[str]


class AnalyticsWindow(BaseModel):
    """Analytics time window for paper submission aggregation."""
    
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime
    submission_rate: float
    avg_plagiarism: float
    avg_ai_probability: float
    spike_detected: bool


class Notification(BaseModel):
    """Notification model for event payloads."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    message: str
    created_at: datetime


# Helper functions for encoding/decoding event payloads

def encode(model: BaseModel) -> str:
    """Encode a Pydantic model to JSON string.
    
    Args:
        model: Pydantic model instance
        
    Returns:
        JSON string representation
    """
    return model.model_dump_json()


def decode(model_class: type[BaseModel], payload: str | bytes | dict) -> BaseModel:
    """Decode JSON payload to a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to decode into
        payload: JSON string, bytes, or dict to decode
        
    Returns:
        Instance of the Pydantic model
    """
    if isinstance(payload, dict):
        return model_class.model_validate(payload)
    elif isinstance(payload, bytes):
        return model_class.model_validate_json(payload.decode('utf-8'))
    else:
        return model_class.model_validate_json(payload)
"""Event schemas and Kafka utilities."""
from .schemas import User, Submission, PlagiarismResult, AnalyticsWindow, Notification
from .kafka import emit_event, get_emitter

__all__ = [
    "User",
    "Submission", 
    "PlagiarismResult",
    "AnalyticsWindow",
    "Notification",
    "emit_event",
    "get_emitter",
]

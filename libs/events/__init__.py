"""Event schemas and Kafka utilities.

This package provides:
- Pydantic models for event payloads (User, Submission, PlagiarismResult, etc.)
- KafkaEmitter stub for event-driven architecture
- Helper functions for encoding/decoding event payloads
"""
from .schemas import (
    User,
    Submission,
    PlagiarismResult,
    AnalyticsWindow,
    Notification,
    encode,
    decode,
)
from .kafka import emit_event, get_emitter, KafkaEmitter

__all__ = [
    # Models
    "User",
    "Submission",
    "PlagiarismResult",
    "AnalyticsWindow",
    "Notification",
    # Encoding/Decoding helpers
    "encode",
    "decode",
    # Kafka utilities
    "emit_event",
    "get_emitter",
    "KafkaEmitter",
]

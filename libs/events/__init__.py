"""Event schemas and Kafka utilities.

This package provides:
- Pydantic models for event payloads (User, Submission, PlagiarismResult, etc.)
- KafkaProducerClient and KafkaConsumerClient for clean Kafka integration
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
from .kafka import KafkaProducerClient, KafkaConsumerClient

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
    # Kafka clients
    "KafkaProducerClient",
    "KafkaConsumerClient",
]

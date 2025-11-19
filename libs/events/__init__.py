"""Event schemas and data models.

This package provides Pydantic models for event payloads used across services.

For Kafka utilities, use:
- from libs.kafka import KafkaProducerClient, KafkaConsumerClient, KafkaStreamProcessor

For backward compatibility, Kafka clients are still accessible from here:
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
# Backward compatibility imports (deprecated - use libs.kafka instead)
from libs.kafka.client import KafkaProducerClient, KafkaConsumerClient

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
    # Kafka clients (backward compatibility)
    "KafkaProducerClient",
    "KafkaConsumerClient",
]

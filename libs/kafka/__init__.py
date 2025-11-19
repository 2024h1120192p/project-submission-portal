"""Kafka integration library.

Provides clean interfaces for Kafka producers, consumers, and stream processors.
"""
from .client import KafkaProducerClient, KafkaConsumerClient
from .processor import KafkaStreamProcessor

__all__ = [
    "KafkaProducerClient",
    "KafkaConsumerClient",
    "KafkaStreamProcessor",
]

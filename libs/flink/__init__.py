"""Flink stream processing library.

Provides abstractions for time-based windowed aggregations using Flink,
as well as REST API client for job management and monitoring.
"""
from .client import FlinkClient
from .flink import FlinkStreamProcessor

__all__ = [
    "FlinkClient",
    "FlinkStreamProcessor",
]

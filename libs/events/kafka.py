"""Event emission utilities for Kafka messaging."""
from typing import Any, Dict
import json


class KafkaEmitter:
    """Stub Kafka emitter for event-driven architecture.
    
    In production, replace with actual Kafka producer using confluent-kafka or aiokafka.
    """
    
    def __init__(self, broker: str = "localhost:9092"):
        self.broker = broker
        # TODO: Initialize actual Kafka producer
        # from confluent_kafka import Producer
        # self.producer = Producer({'bootstrap.servers': broker})
    
    def emit(self, topic: str, event: Dict[str, Any]) -> None:
        """Emit an event to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            event: Event data as dictionary
        """
        # Stub implementation - prints to console
        print(f"[KAFKA_EMIT] Topic: {topic}")
        print(f"[KAFKA_EMIT] Event: {json.dumps(event, default=str)}")
        
        # TODO: Replace with actual Kafka producer
        # self.producer.produce(topic, json.dumps(event, default=str))
        # self.producer.flush()


# Global emitter instance
_emitter: KafkaEmitter | None = None


def get_emitter() -> KafkaEmitter:
    """Get or create global Kafka emitter instance."""
    global _emitter
    if _emitter is None:
        _emitter = KafkaEmitter()
    return _emitter


def emit_event(topic: str, event: Dict[str, Any]) -> None:
    """Convenience function to emit an event."""
    get_emitter().emit(topic, event)

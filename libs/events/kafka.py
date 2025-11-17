"""Event emission utilities for Kafka messaging.

Provides a KafkaEmitter stub that can be replaced with actual Kafka implementation.
All functions are async-compatible and can be used in async contexts.
"""
from typing import Any, Dict
import json


class KafkaEmitter:
    """Stub Kafka emitter for event-driven architecture.
    
    This is a stub implementation that prints events to console.
    In production, replace with actual Kafka producer using confluent-kafka or aiokafka.
    
    The stub is designed to be async-compatible so it can be seamlessly replaced
    with an async Kafka client when needed.
    """
    
    def __init__(self, broker: str = "localhost:9092"):
        """Initialize the Kafka emitter.
        
        Args:
            broker: Kafka broker address (default: localhost:9092)
        """
        self.broker = broker
        # TODO: Initialize actual Kafka producer
        # For async implementation:
        # from aiokafka import AIOKafkaProducer
        # self.producer = AIOKafkaProducer(bootstrap_servers=broker)
        # await self.producer.start()
        
        # For sync implementation:
        # from confluent_kafka import Producer
        # self.producer = Producer({'bootstrap.servers': broker})
    
    def emit(self, topic: str, event: Dict[str, Any]) -> None:
        """Emit an event to a Kafka topic (synchronous stub).
        
        Args:
            topic: Kafka topic name
            event: Event data as dictionary
        """
        # Stub implementation - prints to console
        print(f"[KAFKA_EMIT] Topic: {topic}")
        print(f"[KAFKA_EMIT] Event: {json.dumps(event, default=str)}")
        
        # TODO: Replace with actual Kafka producer
        # For sync:
        # self.producer.produce(topic, json.dumps(event, default=str).encode('utf-8'))
        # self.producer.flush()
    
    async def emit_async(self, topic: str, event: Dict[str, Any]) -> None:
        """Emit an event to a Kafka topic (async stub).
        
        This method is provided for async compatibility. Currently it's a stub
        that calls the synchronous emit method.
        
        Args:
            topic: Kafka topic name
            event: Event data as dictionary
        """
        # Stub implementation - calls sync version
        self.emit(topic, event)
        
        # TODO: Replace with actual async Kafka producer
        # await self.producer.send_and_wait(topic, json.dumps(event, default=str).encode('utf-8'))
    
    def close(self) -> None:
        """Close the Kafka producer connection."""
        # TODO: Implement cleanup
        # if hasattr(self, 'producer'):
        #     self.producer.close()
        pass
    
    async def close_async(self) -> None:
        """Close the Kafka producer connection (async)."""
        # TODO: Implement async cleanup
        # if hasattr(self, 'producer'):
        #     await self.producer.stop()
        pass


# Global emitter instance
_emitter: KafkaEmitter | None = None


def get_emitter() -> KafkaEmitter:
    """Get or create global Kafka emitter instance.
    
    Returns:
        Singleton KafkaEmitter instance
    """
    global _emitter
    if _emitter is None:
        _emitter = KafkaEmitter()
    return _emitter


def emit_event(topic: str, event: Dict[str, Any]) -> None:
    """Convenience function to emit an event synchronously.
    
    Args:
        topic: Kafka topic name
        event: Event data as dictionary
    """
    get_emitter().emit(topic, event)


async def emit_event_async(topic: str, event: Dict[str, Any]) -> None:
    """Convenience function to emit an event asynchronously.
    
    Args:
        topic: Kafka topic name
        event: Event data as dictionary
    """
    await get_emitter().emit_async(topic, event)

"""Kafka producer and consumer clients.

Provides clean interfaces for producing and consuming Kafka events.
"""
from typing import Dict, Any, List, Callable, Optional
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from config.logging import get_logger

logger = get_logger(__name__)


class KafkaProducerClient:
    """Kafka producer client with clean interface for event emission.
    
    Usage:
        producer = KafkaProducerClient(broker="kafka:29092")
        await producer.start()
        await producer.emit("topic", {"key": "value"})
        await producer.close()
    """
    
    def __init__(self, broker: str = "localhost:9092"):
        """Initialize Kafka producer client.
        
        Args:
            broker: Kafka broker address
        """
        self.broker = broker
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False
    
    async def start(self) -> None:
        """Start the Kafka producer connection."""
        if self._started:
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.broker,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            await self.producer.start()
            self._started = True
            logger.info(f"Kafka producer connected to {self.broker}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise
    
    async def emit(self, topic: str, event: Dict[str, Any]) -> None:
        """Emit an event to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            event: Event data as dictionary
            
        Raises:
            RuntimeError: If producer not started
        """
        if not self._started or self.producer is None:
            raise RuntimeError("Producer not started. Call await client.start() first.")
        
        try:
            await self.producer.send_and_wait(topic, value=event)
            logger.info(f"Event emitted to topic '{topic}'")
            logger.debug(f"Event data: {event}")
        except Exception as e:
            logger.error(f"Failed to emit event to topic '{topic}': {e}")
            raise
    
    async def close(self) -> None:
        """Close the Kafka producer connection."""
        if self.producer is not None and self._started:
            try:
                await self.producer.stop()
                self._started = False
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
                raise


class KafkaConsumerClient:
    """Kafka consumer client with clean interface for event consumption.
    
    Usage:
        consumer = KafkaConsumerClient(
            broker="kafka:29092",
            group_id="my-service",
            topics=["topic1", "topic2"]
        )
        consumer.register_handler("topic1", my_handler_func)
        await consumer.start()
        await consumer.consume()  # Runs indefinitely
    """
    
    def __init__(
        self,
        broker: str = "kafka:29092",
        group_id: str = "default-group",
        topics: Optional[List[str]] = None
    ):
        """Initialize Kafka consumer client.
        
        Args:
            broker: Kafka broker address
            group_id: Consumer group ID for offset tracking
            topics: List of topics to subscribe to
        """
        self.broker = broker
        self.group_id = group_id
        self.topics = topics or []
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._started = False
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, topic: str, handler: Callable) -> None:
        """Register an event handler for a topic.
        
        Args:
            topic: Kafka topic name
            handler: Async callable that accepts event dict as parameter
        """
        self.handlers[topic] = handler
        logger.info(f"Handler registered for topic '{topic}'")
    
    async def start(self) -> None:
        """Start the Kafka consumer connection."""
        if self._started:
            return
        
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.broker,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
            )
            await self.consumer.start()
            self._started = True
            logger.info(f"Kafka consumer started (group: {self.group_id}, topics: {self.topics})")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise
    
    async def consume(self) -> None:
        """Start consuming messages and dispatch to registered handlers.
        
        This method runs indefinitely, listening for messages.
        Call this in a background task.
        """
        if not self._started or self.consumer is None:
            raise RuntimeError("Consumer not started. Call await client.start() first.")
        
        try:
            async for message in self.consumer:
                topic = message.topic
                event = message.value
                
                logger.debug(f"Event received from topic '{topic}': {event}")
                
                if topic in self.handlers:
                    try:
                        await self.handlers[topic](event)
                    except Exception as e:
                        logger.error(f"Error in handler for topic '{topic}': {e}", exc_info=True)
                else:
                    logger.warning(f"No handler registered for topic '{topic}'")
        except Exception as e:
            logger.error(f"Error consuming from Kafka: {e}", exc_info=True)
            raise
    
    async def close(self) -> None:
        """Close the Kafka consumer connection."""
        if self.consumer is not None and self._started:
            try:
                await self.consumer.stop()
                self._started = False
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
                raise

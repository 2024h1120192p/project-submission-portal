"""Kafka stream processors.

Provides abstract base class for Kafka-based stream processing with
consume/process/produce pattern.
"""
from typing import List, Optional
import json
import asyncio
from abc import ABC, abstractmethod
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from config.logging import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class KafkaStreamProcessor(ABC):
    """Abstract base class for Kafka stream processors.
    
    Handles common boilerplate for consuming from input topics,
    processing events, and producing to output topics.
    
    Subclasses should implement process_event() method with business logic.
    
    Usage:
        class MyStreamProcessor(KafkaStreamProcessor):
            async def process_event(self, event: dict) -> dict:
                # Your business logic
                event['processed'] = True
                return event
        
        processor = MyStreamProcessor(
            input_topics=['input'],
            output_topic='output',
            group_id='my-group',
            kafka_broker='kafka:29092'
        )
        await processor.start()
        await processor.run()  # Blocks until stopped
        await processor.stop()
    """
    
    def __init__(
        self,
        input_topics: List[str],
        output_topic: str,
        group_id: str,
        kafka_broker: str = None
    ):
        """Initialize the stream processor.
        
        Args:
            input_topics: List of topics to consume from
            output_topic: Topic to produce processed events to
            group_id: Kafka consumer group ID
            kafka_broker: Kafka broker address (defaults to settings.KAFKA_BROKER if not provided)
        """
        if kafka_broker is None:
            kafka_broker = settings.KAFKA_BROKER
        self.input_topics = input_topics
        self.output_topic = output_topic
        self.group_id = group_id
        self.kafka_broker = kafka_broker
        
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def process_event(self, event: dict) -> dict:
        """Process a single event from input topic.
        
        Subclasses must implement this method with their business logic.
        
        Args:
            event: Event dictionary from Kafka
            
        Returns:
            Processed event dictionary
        """
        pass
    
    async def _process_messages(self) -> None:
        """Continuously consume and process messages from input topics."""
        try:
            async for msg in self.consumer:
                try:
                    # Decode event
                    event = json.loads(msg.value.decode('utf-8'))
                    logger.debug(f"Event received from topic '{msg.topic}'")
                    
                    # Process event with subclass implementation
                    processed = await self.process_event(event)
                    
                    # Send to output topic
                    await self.producer.send_and_wait(
                        self.output_topic,
                        value=processed
                    )
                    logger.debug(f"Processed event sent to topic '{self.output_topic}'")
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    
        except asyncio.CancelledError:
            logger.info("Stream processor task cancelled")
            raise
    
    async def start(self) -> None:
        """Start the stream processor (initialize connections and begin processing)."""
        try:
            logger.info(f"Starting stream processor (group: {self.group_id})...")
            
            # Create consumer
            self.consumer = AIOKafkaConsumer(
                *self.input_topics,
                bootstrap_servers=self.kafka_broker,
                group_id=self.group_id,
                value_deserializer=lambda m: m,  # Keep as bytes, decode in process
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            
            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_broker,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
            )
            
            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()
            
            self.running = True
            
            # Start message processing in background task
            self.task = asyncio.create_task(self._process_messages())
            logger.info("Stream processor started and processing messages")
            
        except Exception as e:
            logger.error(f"Failed to start stream processor: {e}")
            raise
    
    async def run(self) -> None:
        """Wait for the stream processor to complete (blocks indefinitely).
        
        This is optional - the processor runs automatically after start().
        Use this if you want to wait for completion, though it typically
        only completes on cancellation or error.
        """
        if self.task is None:
            raise RuntimeError("Processor not started. Call await start() first.")
        
        try:
            await self.task
        except asyncio.CancelledError:
            logger.info("Stream processor run loop cancelled")
    
    async def stop(self) -> None:
        """Stop the stream processor."""
        try:
            logger.info("Stopping stream processor...")
            self.running = False
            
            # Cancel processing task
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
            
            # Stop consumer and producer
            if self.consumer:
                await self.consumer.stop()
            if self.producer:
                await self.producer.stop()
                
            logger.info("Stream processor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream processor: {e}")

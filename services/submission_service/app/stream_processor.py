"""Stream processor for submission service using aiokafka.

Consumes paper_uploaded events from Kafka, enriches with metadata,
and writes to paper_uploaded_processed topic.
"""
import json
import asyncio
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from config.logging import get_logger

logger = get_logger(__name__)


class SubmissionStreamProcessor:
    """Async stream processor for submission service using aiokafka."""
    
    def __init__(self, kafka_broker: str = 'kafka:29092'):
        """Initialize the stream processor.
        
        Args:
            kafka_broker: Kafka broker address
        """
        self.kafka_broker = kafka_broker
        self.consumer = None
        self.producer = None
        self.running = False
        self.task = None
        
    async def enrich_event(self, event: dict) -> dict:
        """Enrich submission event with processing metadata.
        
        Args:
            event: Submission event dictionary
            
        Returns:
            Enriched event dictionary
        """
        # Add processing metadata (minimal - no business logic)
        event['processed_at'] = datetime.utcnow().isoformat()
        event['event_type'] = 'paper_uploaded'
        event['processing_pipeline'] = 'submission-service'
        
        # Extract text length for analytics (derived metric, not business logic)
        if 'text' in event:
            event['text_length'] = len(event.get('text', ''))
        
        return event
    
    async def process_messages(self):
        """Continuously process messages from Kafka."""
        try:
            async for msg in self.consumer:
                try:
                    # Decode and enrich event
                    event = json.loads(msg.value.decode('utf-8'))
                    enriched = await self.enrich_event(event)
                    
                    # Send to processed topic
                    await self.producer.send(
                        'paper_uploaded_processed',
                        json.dumps(enriched).encode('utf-8')
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing submission event: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Stream processor task cancelled")
            raise
    
    async def start(self):
        """Start the stream processor."""
        try:
            logger.info("Starting submission stream processor with aiokafka...")
            
            # Create consumer
            self.consumer = AIOKafkaConsumer(
                'paper_uploaded',
                bootstrap_servers=self.kafka_broker,
                group_id='submission-service-stream-processor',
                value_deserializer=lambda m: m,  # Keep as bytes, decode manually
                auto_offset_reset='earliest'
            )
            
            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_broker,
                value_serializer=lambda v: v  # Keep as bytes, encode manually
            )
            
            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()
            
            self.running = True
            # Start processing task
            self.task = asyncio.create_task(self.process_messages())
            
            logger.info("Submission stream processor started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start submission stream processor: {e}")
            raise
    
    async def stop(self):
        """Stop the stream processor."""
        try:
            logger.info("Stopping submission stream processor...")
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
                
            logger.info("Submission stream processor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream processor: {e}")


def create_stream_processor(kafka_broker: str = 'kafka:29092') -> SubmissionStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        Configured SubmissionStreamProcessor instance
    """
    return SubmissionStreamProcessor(kafka_broker=kafka_broker)

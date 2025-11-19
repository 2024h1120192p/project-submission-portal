"""Stream processor for plagiarism service using aiokafka.

Consumes plagiarism_checked events from Kafka (already enriched by service),
and writes to plagiarism_checked_processed topic for analytics.
"""
import json
import asyncio
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from config.logging import get_logger

logger = get_logger(__name__)


class PlagiarismStreamProcessor:
    """Async stream processor for plagiarism service using aiokafka."""
    
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
        
    async def process_event(self, event: dict) -> dict:
        """Add minimal processing metadata to event.
        
        Business logic (severity, requires_review, ai_generated_likely)
        is already set by the plagiarism_service.app.engine.
        
        Args:
            event: Plagiarism event dictionary (already enriched)
            
        Returns:
            Event with processing metadata
        """
        # Add only stream processing metadata
        event['processed_at'] = datetime.utcnow().isoformat()
        event['event_type'] = 'plagiarism_checked'
        event['processing_pipeline'] = 'plagiarism-service'
        
        return event
    
    async def process_messages(self):
        """Continuously process messages from Kafka."""
        try:
            async for msg in self.consumer:
                try:
                    # Decode and process event
                    event = json.loads(msg.value.decode('utf-8'))
                    processed = await self.process_event(event)
                    
                    # Send to processed topic
                    await self.producer.send(
                        'plagiarism_checked_processed',
                        json.dumps(processed).encode('utf-8')
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing plagiarism event: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Stream processor task cancelled")
            raise
    
    async def start(self):
        """Start the stream processor."""
        try:
            logger.info("Starting plagiarism stream processor with aiokafka...")
            
            # Create consumer
            self.consumer = AIOKafkaConsumer(
                'plagiarism_checked',
                bootstrap_servers=self.kafka_broker,
                group_id='plagiarism-service-stream-processor',
                value_deserializer=lambda m: m,
                auto_offset_reset='earliest'
            )
            
            # Create producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_broker,
                value_serializer=lambda v: v
            )
            
            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()
            
            self.running = True
            # Start processing task
            self.task = asyncio.create_task(self.process_messages())
            
            logger.info("Plagiarism stream processor started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start plagiarism stream processor: {e}")
            raise
    
    async def stop(self):
        """Stop the stream processor."""
        try:
            logger.info("Stopping plagiarism stream processor...")
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
                
            logger.info("Plagiarism stream processor stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream processor: {e}")


def create_stream_processor(kafka_broker: str = 'kafka:29092') -> PlagiarismStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        Configured PlagiarismStreamProcessor instance
    """
    return PlagiarismStreamProcessor(kafka_broker=kafka_broker)

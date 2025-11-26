"""Stream processor for plagiarism service using aiokafka.

Consumes plagiarism_checked events from Kafka (already enriched by service),
and writes to plagiarism_checked_processed topic for analytics.
"""
from datetime import datetime
from typing import List
from libs.kafka.processor import KafkaStreamProcessor
from libs.events.schemas import Submission
from .engine import run_plagiarism_pipeline
from .store import store
from config.logging import get_logger

logger = get_logger(__name__)


class SubmissionStreamProcessor(KafkaStreamProcessor):
    """Stream processor for incoming submissions.
    
    Consumes paper_uploaded events, runs plagiarism check,
    and produces plagiarism_checked events.
    """
    
    def __init__(self, kafka_broker: str = 'localhost:9092'):
        super().__init__(
            input_topics=['paper_uploaded'],
            output_topic='plagiarism_checked',
            group_id='plagiarism-service-submission-processor',
            kafka_broker=kafka_broker
        )
    
    async def process_event(self, event: dict) -> dict:
        """Process submission event and run plagiarism check.
        
        Args:
            event: Submission event dictionary
            
        Returns:
            PlagiarismResult dictionary
        """
        try:
            # Parse submission
            sub = Submission(**event)
            
            # Run plagiarism check
            result = await run_plagiarism_pipeline(sub)
            
            # Save result to MongoDB
            await store.save(result)
            
            logger.info(f"Processed submission {sub.id} via Kafka")
            return result.model_dump()
        except Exception as e:
            logger.error(f"Error processing submission event: {e}")
            # Return original event with error flag to avoid crashing
            event['error'] = str(e)
            return event


class PlagiarismStreamProcessor(KafkaStreamProcessor):
    """Stream processor for plagiarism service events.
    
    Processes plagiarism_checked events and forwards them to analytics pipeline.
    Business logic (severity, requires_review, ai_generated_likely)
    is already set by plagiarism_service.app.engine.
    """
    
    def __init__(self, kafka_broker: str = 'localhost:9092'):
        """Initialize the plagiarism stream processor.
        
        Args:
            kafka_broker: Kafka broker address
        """
        super().__init__(
            input_topics=['plagiarism_checked'],
            output_topic='plagiarism_checked_processed',
            group_id='plagiarism-service-stream-processor',
            kafka_broker=kafka_broker
        )
    
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


class CompositeStreamProcessor:
    """Manages multiple stream processors."""
    
    def __init__(self, processors: List[KafkaStreamProcessor]):
        self.processors = processors
        
    async def start(self):
        for p in self.processors:
            await p.start()
            
    async def stop(self):
        for p in self.processors:
            await p.stop()


def create_stream_processor(kafka_broker: str = 'localhost:9092') -> CompositeStreamProcessor:
    """Factory function to create stream processors.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        CompositeStreamProcessor managing both processors
    """
    return CompositeStreamProcessor([
        SubmissionStreamProcessor(kafka_broker=kafka_broker),
        PlagiarismStreamProcessor(kafka_broker=kafka_broker)
    ])

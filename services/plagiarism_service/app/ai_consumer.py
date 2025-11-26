"""AI Plagiarism Kafka consumer for the plagiarism service.

Consumes paper_uploaded_processed events from Kafka and triggers
AI plagiarism detection using OpenAI integration.
"""
from datetime import datetime
from typing import Optional
from libs.kafka.processor import KafkaStreamProcessor
from libs.events.schemas import Submission, PlagiarismResult
from config.logging import get_logger

from .openai_client import get_openai_client
from .engine import run_plagiarism_pipeline
from .store import store

logger = get_logger(__name__)


class AIPlagiarismConsumer(KafkaStreamProcessor):
    """Kafka consumer for AI plagiarism checking.
    
    Consumes paper_uploaded_processed events and triggers AI-based
    plagiarism detection using OpenAI integration.
    
    Flow:
    1. Consume paper_uploaded_processed events
    2. Run plagiarism pipeline with OpenAI AI detection
    3. Store results in MongoDB
    4. Produce plagiarism_checked events for downstream processing
    """
    
    def __init__(self, kafka_broker: str = 'localhost:9092'):
        """Initialize the AI plagiarism consumer.
        
        Args:
            kafka_broker: Kafka broker address
        """
        super().__init__(
            input_topics=['paper_uploaded_processed'],
            output_topic='plagiarism_checked',
            group_id='plagiarism-service-ai-consumer',
            kafka_broker=kafka_broker
        )
        self.openai_client = get_openai_client()
    
    async def process_event(self, event: dict) -> dict:
        """Process uploaded paper event and run AI plagiarism detection.
        
        Args:
            event: Paper uploaded event dictionary
            
        Returns:
            Plagiarism result event dictionary
        """
        logger.info(f"Processing paper for AI plagiarism check: {event.get('id', 'unknown')}")
        
        try:
            # Create Submission object from event
            submission = Submission(
                id=event.get('id', ''),
                user_id=event.get('user_id', ''),
                assignment_id=event.get('assignment_id', ''),
                uploaded_at=event.get('uploaded_at', datetime.utcnow().isoformat()),
                file_url=event.get('file_url', ''),
                text=event.get('text')
            )
            
            # Run plagiarism pipeline (includes OpenAI AI detection)
            result = await run_plagiarism_pipeline(submission)
            
            # Store result in MongoDB
            await store.save(result)
            
            # Convert result to event dictionary
            result_event = result.model_dump(mode='json')
            result_event['source'] = 'kafka_consumer'
            result_event['consumed_from'] = 'paper_uploaded_processed'
            result_event['processed_at'] = datetime.utcnow().isoformat()
            
            logger.info(
                f"AI plagiarism check complete for {submission.id}: "
                f"ai_probability={result.ai_generated_probability:.2f}, "
                f"severity={result.severity}"
            )
            
            return result_event
            
        except Exception as e:
            logger.error(f"Error processing event for AI plagiarism: {e}")
            # Return error event to not block the pipeline
            return {
                'submission_id': event.get('id', 'unknown'),
                'error': str(e),
                'processed_at': datetime.utcnow().isoformat(),
                'event_type': 'plagiarism_check_failed'
            }


def create_ai_plagiarism_consumer(kafka_broker: str = 'localhost:9092') -> AIPlagiarismConsumer:
    """Factory function to create an AI plagiarism consumer instance.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        Configured AIPlagiarismConsumer instance
    """
    return AIPlagiarismConsumer(kafka_broker=kafka_broker)

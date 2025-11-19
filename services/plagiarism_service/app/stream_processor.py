"""Stream processor for plagiarism service using aiokafka.

Consumes plagiarism_checked events from Kafka (already enriched by service),
and writes to plagiarism_checked_processed topic for analytics.
"""
from datetime import datetime
from libs.kafka.processor import KafkaStreamProcessor


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


def create_stream_processor(kafka_broker: str = 'localhost:9092') -> PlagiarismStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        Configured PlagiarismStreamProcessor instance
    """
    return PlagiarismStreamProcessor(kafka_broker=kafka_broker)

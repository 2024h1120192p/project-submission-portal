"""Stream processor for submission service using aiokafka.

Consumes paper_uploaded events from Kafka, enriches with metadata,
and writes to paper_uploaded_processed topic.
"""
from datetime import datetime
from libs.kafka.processor import KafkaStreamProcessor


class SubmissionStreamProcessor(KafkaStreamProcessor):
    """Stream processor for submission service events.
    
    Enriches paper_uploaded events with processing metadata
    and forwards them to analytics pipeline.
    """
    
    def __init__(self, kafka_broker: str = 'localhost:9092'):
        """Initialize the submission stream processor.
        
        Args:
            kafka_broker: Kafka broker address
        """
        super().__init__(
            input_topics=['paper_uploaded'],
            output_topic='paper_uploaded_processed',
            group_id='submission-service-stream-processor',
            kafka_broker=kafka_broker
        )
    
    async def process_event(self, event: dict) -> dict:
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


def create_stream_processor(kafka_broker: str = 'localhost:9092') -> SubmissionStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address
        
    Returns:
        Configured SubmissionStreamProcessor instance
    """
    return SubmissionStreamProcessor(kafka_broker=kafka_broker)

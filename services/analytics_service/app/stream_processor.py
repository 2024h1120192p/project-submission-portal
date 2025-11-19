"""Stream processor for analytics service.

Uses Flink for time-based windowed aggregations (Flink's core strength).
This is the appropriate use case for Flink because:
1. Time-based windowing is complex to implement correctly
2. Flink handles event time, watermarks, and late data arrival
3. State management for windows is built-in

For simple consumption/production, aiokafka is used in other services.
"""
import json
import os
from datetime import datetime
from pyflink.datastream.functions import AggregateFunction
from libs.flink.flink import FlinkStreamProcessor
from config.logging import get_logger

logger = get_logger(__name__)


class AnalyticsAggregator(AggregateFunction):
    """Aggregate analytics data within time windows.
    
    Pure stream processing logic - no business logic, just time-based aggregation.
    """
    
    def create_accumulator(self):
        """Create initial accumulator."""
        return {
            'submission_count': 0,
            'plagiarism_scores_internal': [],
            'plagiarism_scores_external': [],
            'ai_probabilities': [],
            'high_risk_count': 0,
        }
    
    def add(self, value, accumulator):
        """Add value to accumulator."""
        try:
            event = json.loads(value)
            event_type = event.get('event_type', '')
            
            if event_type == 'paper_uploaded':
                accumulator['submission_count'] += 1
                
            elif event_type == 'plagiarism_checked':
                internal = event.get('internal_score', 0.0)
                external = event.get('external_score', 0.0)
                ai_prob = event.get('ai_generated_probability', 0.0)
                
                accumulator['plagiarism_scores_internal'].append(internal)
                accumulator['plagiarism_scores_external'].append(external)
                accumulator['ai_probabilities'].append(ai_prob)
                
                # Count high risk (based on business logic from service)
                if event.get('severity') == 'high':
                    accumulator['high_risk_count'] += 1
            
            return accumulator
        except Exception as e:
            logger.error(f"Error in aggregator: {e}")
            return accumulator
    
    def get_result(self, accumulator):
        """Get aggregation result."""
        internal_scores = accumulator['plagiarism_scores_internal']
        external_scores = accumulator['plagiarism_scores_external']
        ai_probs = accumulator['ai_probabilities']
        
        avg_internal = sum(internal_scores) / len(internal_scores) if internal_scores else 0.0
        avg_external = sum(external_scores) / len(external_scores) if external_scores else 0.0
        avg_ai = sum(ai_probs) / len(ai_probs) if ai_probs else 0.0
        
        result = {
            'window_start': datetime.utcnow().isoformat(),
            'submission_count': accumulator['submission_count'],
            'avg_internal_score': avg_internal,
            'avg_external_score': avg_external,
            'avg_ai_probability': avg_ai,
            'high_risk_count': accumulator['high_risk_count'],
            'total_checks': len(internal_scores)
        }
        
        return json.dumps(result)
    
    def merge(self, acc1, acc2):
        """Merge two accumulators."""
        return {
            'submission_count': acc1['submission_count'] + acc2['submission_count'],
            'plagiarism_scores_internal': acc1['plagiarism_scores_internal'] + acc2['plagiarism_scores_internal'],
            'plagiarism_scores_external': acc1['plagiarism_scores_external'] + acc2['plagiarism_scores_external'],
            'ai_probabilities': acc1['ai_probabilities'] + acc2['ai_probabilities'],
            'high_risk_count': acc1['high_risk_count'] + acc2['high_risk_count'],
        }


class AnalyticsStreamProcessor(FlinkStreamProcessor):
    """Flink-based windowed analytics processor.
    
    Extends FlinkStreamProcessor for time-based windowed aggregations
    of submission and plagiarism check events.
    """
    
    def __init__(self, kafka_broker: str = 'localhost:9092', window_minutes: int = 5):
        """Initialize the analytics stream processor.
        
        Args:
            kafka_broker: Kafka broker address
            window_minutes: Window size in minutes for tumbling windows
        """
        super().__init__(
            kafka_broker=kafka_broker,
            window_minutes=window_minutes,
            output_topic='analytics_window',
            group_id='analytics-service-flink-processor',
            job_name='Analytics Windowed Aggregation'
        )
    
    def get_aggregator(self) -> AggregateFunction:
        """Get the aggregator for analytics windowing.
        
        Returns:
            Configured AnalyticsAggregator instance
        """
        return AnalyticsAggregator()
    
    def configure_sources(self) -> list:
        """Configure Kafka sources for analytics streams.
        
        Consumes both submission and plagiarism processed events.
        
        Returns:
            List of (topic_name, KafkaSource) tuples
        """
        submission_source = self._build_kafka_source('paper_uploaded_processed')
        plagiarism_source = self._build_kafka_source('plagiarism_checked_processed')
        
        return [
            ('paper_uploaded_processed', submission_source),
            ('plagiarism_checked_processed', plagiarism_source)
        ]


def create_stream_processor(kafka_broker: str = None, window_minutes: int = 5) -> AnalyticsStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address (defaults to 'kafka:29092')
        window_minutes: Window size in minutes for aggregations
        
    Returns:
        Configured AnalyticsStreamProcessor instance
    """
    if kafka_broker is None:
        kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
    
    return AnalyticsStreamProcessor(kafka_broker=kafka_broker, window_minutes=window_minutes)

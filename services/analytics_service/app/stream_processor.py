"""Stream processor for analytics service.

Uses Flink ONLY for time-based windowed aggregations (unavoidable - Flink's core strength).
This is the one place where Flink is justified because:
1. Time-based windowing is complex to implement correctly
2. Flink handles event time, watermarks, and late data arrival
3. State management for windows is built-in

For simple consumption/production, we use aiokafka everywhere else.
"""
import json
import os
from datetime import datetime
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    KafkaSource, KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema
)
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream.functions import AggregateFunction
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common import Time, WatermarkStrategy, Duration
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


class AnalyticsStreamProcessor:
    """Flink-based windowed analytics processor.
    
    JUSTIFICATION for using Flink here (not aiokafka):
    - Time-based windowing is Flink's core feature
    - Handling event time, watermarks, and late data is complex
    - State management across windows requires specialized infrastructure
    - Tumbling/sliding/session windows are built-in
    - Alternative would be custom implementation with Redis/state store (more complex)
    """
    
    def __init__(self, kafka_broker: str = 'kafka:29092', window_minutes: int = 5):
        """Initialize the stream processor.
        
        Args:
            kafka_broker: Kafka broker address
            window_minutes: Window size in minutes for tumbling windows
        """
        self.kafka_broker = kafka_broker
        self.window_minutes = window_minutes
        self.env = None
        
    def create_pipeline(self) -> StreamExecutionEnvironment:
        """Create and configure the Flink streaming pipeline with windowing.
        
        Returns:
            Configured Flink execution environment
        """
        # Create execution environment
        self.env = StreamExecutionEnvironment.get_execution_environment()
        self.env.set_parallelism(1)
        
        # Add Kafka connector JARs
        kafka_jar = "flink-sql-connector-kafka-1.18.0.jar"
        self.env.add_jars(f"file:///opt/flink/lib/{kafka_jar}")
        
        # Configure Kafka sources for both processed topics
        submission_source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_broker) \
            .set_topics("paper_uploaded_processed") \
            .set_group_id("analytics-service-flink-processor") \
            .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()
        
        plagiarism_source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_broker) \
            .set_topics("plagiarism_checked_processed") \
            .set_group_id("analytics-service-flink-processor") \
            .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()
        
        # Configure Kafka sink for aggregated analytics
        kafka_sink = KafkaSink.builder() \
            .set_bootstrap_servers(self.kafka_broker) \
            .set_record_serializer(
                KafkaRecordSerializationSchema.builder()
                .set_topic("analytics_window")
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
            ) \
            .build()
        
        # Build processing pipeline with streams
        submission_stream = self.env.from_source(
            submission_source,
            WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(5)),
            "Kafka Source - submissions"
        )
        
        plagiarism_stream = self.env.from_source(
            plagiarism_source,
            WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(5)),
            "Kafka Source - plagiarism"
        )
        
        # Union streams for combined analytics
        union_stream = submission_stream.union(plagiarism_stream)
        
        # Apply windowed aggregation (tumbling windows)
        # THIS is why we use Flink - time-based windowing is its killer feature
        aggregated_stream = union_stream \
            .key_by(lambda x: "global") \
            .window(TumblingProcessingTimeWindows.of(Time.minutes(self.window_minutes))) \
            .aggregate(AnalyticsAggregator(), output_type=Types.STRING())
        
        # Sink to analytics topic
        aggregated_stream.sink_to(kafka_sink)
        
        logger.info(f"Analytics Flink pipeline created with {self.window_minutes}-min windows")
        return self.env
    
    async def start(self):
        """Start the stream processor asynchronously."""
        try:
            logger.info("Starting analytics Flink processor for windowed aggregations...")
            env = self.create_pipeline()
            # Run in background
            env.execute_async("Analytics Windowed Aggregation")
            logger.info("Analytics Flink processor started successfully")
        except Exception as e:
            logger.error(f"Failed to start analytics Flink processor: {e}")
            raise
    
    async def stop(self):
        """Stop the stream processor."""
        try:
            logger.info("Stopping analytics Flink processor...")
            # Flink cleanup
            logger.info("Analytics Flink processor stopped")
        except Exception as e:
            logger.error(f"Error stopping Flink processor: {e}")


def create_stream_processor(kafka_broker: str = None, window_minutes: int = 5) -> AnalyticsStreamProcessor:
    """Factory function to create a stream processor instance.
    
    Args:
        kafka_broker: Kafka broker address (defaults to 'kafka:29092')
        window_minutes: Window size in minutes for aggregations
        
    Returns:
        Configured AnalyticsStreamProcessor instance
    """
    if kafka_broker is None:
        kafka_broker = os.getenv('KAFKA_BROKER', 'kafka:29092')
    
    return AnalyticsStreamProcessor(kafka_broker=kafka_broker, window_minutes=window_minutes)

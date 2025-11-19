"""Flink stream processor interfaces for windowed aggregations.

Provides clean, reusable base class for Flink-based stream processing
with time-based windowing, following the same pattern as Kafka clients.

Flink is only used for:
- Time-based windowing (tumbling, sliding, session windows)
- Event time processing with watermarks
- Stateful aggregations across time windows
- Complex event processing (CEP) patterns
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import os
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


class FlinkStreamProcessor(ABC):
    """Abstract base class for Flink stream processors with windowed aggregations.
    
    Handles common boilerplate for setting up Flink pipelines with Kafka sources/sinks
    and time-based windowing. Subclasses implement the aggregator logic.
    
    Usage:
        class MyAggregator(AggregateFunction):
            def create_accumulator(self):
                return {}
            def add(self, value, accumulator):
                # Your aggregation logic
                return accumulator
            def get_result(self, accumulator):
                return json.dumps(result)
            def merge(self, acc1, acc2):
                # Merge logic
                return merged_acc
        
        class MyFlinkProcessor(FlinkStreamProcessor):
            def get_aggregator(self) -> AggregateFunction:
                return MyAggregator()
            
            def configure_sources(self):
                # Return list of (topic, KafkaSource)
                return [("input_topic", source1)]
        
        processor = MyFlinkProcessor(
            kafka_broker='kafka:29092',
            window_minutes=5,
            output_topic='output'
        )
        await processor.start()
        await processor.stop()
    """
    
    def __init__(
        self,
        kafka_broker: str = "kafka:29092",
        window_minutes: int = 5,
        output_topic: str = "output",
        group_id: str = "flink-processor-group",
        job_name: str = "Flink Stream Processor"
    ):
        """Initialize the Flink stream processor.
        
        Args:
            kafka_broker: Kafka broker address
            window_minutes: Window size in minutes for tumbling windows
            output_topic: Kafka topic to send aggregated results to
            group_id: Kafka consumer group ID
            job_name: Name for the Flink job
        """
        self.kafka_broker = kafka_broker
        self.window_minutes = window_minutes
        self.output_topic = output_topic
        self.group_id = group_id
        self.job_name = job_name
        self.env: Optional[StreamExecutionEnvironment] = None
    
    @abstractmethod
    def get_aggregator(self) -> AggregateFunction:
        """Get the aggregator function for windowed aggregations.
        
        Subclasses must implement this method.
        
        Returns:
            Configured AggregateFunction instance
        """
        pass
    
    @abstractmethod
    def configure_sources(self) -> List[tuple]:
        """Configure Kafka sources for the pipeline.
        
        Subclasses must implement this method to define input streams.
        
        Returns:
            List of tuples (topic_name, KafkaSource)
        """
        pass
    
    def _build_kafka_source(
        self,
        topic: str,
        name: str = None
    ) -> KafkaSource:
        """Build a Kafka source for a given topic.
        
        Args:
            topic: Kafka topic to consume from
            name: Optional name for the source
            
        Returns:
            Configured KafkaSource
        """
        if name is None:
            name = f"Kafka Source - {topic}"
        
        source = KafkaSource.builder() \
            .set_bootstrap_servers(self.kafka_broker) \
            .set_topics(topic) \
            .set_group_id(self.group_id) \
            .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()
        
        logger.debug(f"Built Kafka source for topic '{topic}'")
        return source
    
    def _build_kafka_sink(self) -> KafkaSink:
        """Build a Kafka sink for the output topic.
        
        Returns:
            Configured KafkaSink
        """
        sink = KafkaSink.builder() \
            .set_bootstrap_servers(self.kafka_broker) \
            .set_record_serializer(
                KafkaRecordSerializationSchema.builder()
                .set_topic(self.output_topic)
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
            ) \
            .build()
        
        logger.debug(f"Built Kafka sink for topic '{self.output_topic}'")
        return sink
    
    def _create_pipeline(self) -> StreamExecutionEnvironment:
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
        
        logger.info(f"Creating Flink pipeline with {self.window_minutes}-minute windows")
        
        # Get configured sources from subclass
        sources = self.configure_sources()
        
        if not sources:
            raise ValueError("No Kafka sources configured. Implement configure_sources()")
        
        # Create streams from sources
        streams = []
        for topic, source in sources:
            stream = self.env.from_source(
                source,
                WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(5)),
                f"Kafka Source - {topic}"
            )
            streams.append(stream)
            logger.debug(f"Added source stream for topic '{topic}'")
        
        # Union all streams if multiple
        if len(streams) == 1:
            union_stream = streams[0]
        else:
            union_stream = streams[0]
            for stream in streams[1:]:
                union_stream = union_stream.union(stream)
            logger.debug(f"Unioned {len(streams)} source streams")
        
        # Apply windowed aggregation (tumbling windows)
        aggregator = self.get_aggregator()
        aggregated_stream = union_stream \
            .key_by(lambda x: "global") \
            .window(TumblingProcessingTimeWindows.of(Time.minutes(self.window_minutes))) \
            .aggregate(aggregator, output_type=Types.STRING())
        
        logger.debug("Applied windowed aggregation")
        
        # Sink to output topic
        kafka_sink = self._build_kafka_sink()
        aggregated_stream.sink_to(kafka_sink)
        
        logger.info(f"Flink pipeline created successfully")
        return self.env
    
    async def start(self) -> None:
        """Start the Flink stream processor.
        
        Creates and executes the Flink pipeline in async mode.
        """
        try:
            logger.info(f"Starting Flink processor: {self.job_name}")
            
            env = self._create_pipeline()
            
            # Run pipeline asynchronously
            env.execute_async(self.job_name)
            
            logger.info(f"Flink processor '{self.job_name}' started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Flink processor: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the Flink stream processor.
        
        Performs cleanup and graceful shutdown.
        """
        try:
            logger.info(f"Stopping Flink processor: {self.job_name}")
            
            # Flink cleanup (if needed in future)
            # Currently, Flink manages its own lifecycle
            
            logger.info(f"Flink processor '{self.job_name}' stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Flink processor: {e}")

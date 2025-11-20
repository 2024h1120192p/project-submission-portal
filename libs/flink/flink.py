"""Flink stream processor interfaces for windowed aggregations.

Provides clean, reusable base class for Flink-based stream processing
with time-based windowing, following the same pattern as Kafka clients.

Supports three execution modes:
1. LOCAL: Embedded mini-cluster in the same process (dev/testing only)
2. REMOTE: Self-hosted Flink cluster (deployed in Docker/K8s)
3. MANAGED: Fully managed Flink service (AWS Kinesis, Confluent Cloud, etc.)

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
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


def _create_flink_env(
    mode: str = "local",
    host: str = "flink-jobmanager",
    port: int = 8081,
    managed_endpoint: str = None,
    managed_api_key: str = None
) -> StreamExecutionEnvironment:
    """Create a Flink execution environment based on deployment mode.
    
    Args:
        mode: Execution mode - "local", "remote", or "managed"
        host: Flink JobManager hostname/IP (for remote mode)
        port: Flink JobManager REST API port (for remote mode)
        managed_endpoint: Managed Flink service endpoint (for managed mode)
        managed_api_key: API key for managed service authentication
        
    Returns:
        Configured StreamExecutionEnvironment
    """
    env = StreamExecutionEnvironment.get_execution_environment()
    
    if mode == "local":
        # Local mini-cluster (embedded in process) - for development only
        logger.info("Creating LOCAL Flink environment (mini-cluster)")
        logger.warning("Local mode is NOT production-ready. Use remote or managed mode.")
        # Local environment is the default
        
    elif mode == "remote":
        # Self-hosted Flink cluster (Docker/K8s)
        logger.info(f"Creating REMOTE Flink environment pointing to {host}:{port}")
        env.get_config().set_string("jobmanager.rpc.address", host)
        env.get_config().set_string("jobmanager.rpc.port", str(port))
        
    elif mode == "managed":
        # Fully managed Flink service (AWS Kinesis, Confluent Cloud, etc.)
        logger.info(f"Creating MANAGED Flink environment pointing to {managed_endpoint}")
        if not managed_endpoint:
            raise ValueError("Managed endpoint required for managed mode")
        
        # Configure for managed service
        # Note: Specific configuration depends on the managed service provider
        # For AWS Kinesis Data Analytics:
        env.get_config().set_string("execution.target", "kinesis")
        env.get_config().set_string("kinesis.analytics.endpoint", managed_endpoint)
        
        # For Confluent Cloud:
        # env.get_config().set_string("execution.target", "confluent-cloud")
        # env.get_config().set_string("confluent.cloud.endpoint", managed_endpoint)
        
        if managed_api_key:
            env.get_config().set_string("security.credentials.api-key", managed_api_key)
    
    else:
        raise ValueError(f"Invalid Flink mode: {mode}. Must be 'local', 'remote', or 'managed'")
    
    return env


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
        kafka_broker: str = None,
        window_minutes: int = 5,
        output_topic: str = "output",
        group_id: str = "flink-processor-group",
        job_name: str = "Flink Stream Processor",
        flink_mode: str = None,
        flink_host: str = None,
        flink_port: int = None,
        flink_managed_endpoint: str = None,
        flink_managed_api_key: str = None
    ):
        """Initialize the Flink stream processor.
        
        Args:
            kafka_broker: Kafka broker address (defaults to settings.KAFKA_BROKER)
            window_minutes: Window size in minutes for tumbling windows
            output_topic: Kafka topic to send aggregated results to
            group_id: Kafka consumer group ID
            job_name: Name for the Flink job
            flink_mode: Execution mode - "local", "remote", or "managed" (defaults to settings.FLINK_MODE)
            flink_host: Flink JobManager hostname/IP (defaults to settings.FLINK_JOBMANAGER_HOST)
            flink_port: Flink JobManager REST API port (defaults to settings.FLINK_JOBMANAGER_PORT)
            flink_managed_endpoint: Managed Flink service endpoint (defaults to settings.FLINK_MANAGED_ENDPOINT)
            flink_managed_api_key: API key for managed service (defaults to settings.FLINK_MANAGED_API_KEY)
        """
        # Apply defaults from settings if not provided
        if kafka_broker is None:
            kafka_broker = settings.KAFKA_BROKER
        if flink_mode is None:
            flink_mode = settings.FLINK_MODE
        if flink_host is None:
            flink_host = settings.FLINK_JOBMANAGER_HOST
        if flink_port is None:
            flink_port = settings.FLINK_JOBMANAGER_PORT
        if flink_managed_endpoint is None:
            flink_managed_endpoint = settings.FLINK_MANAGED_ENDPOINT
        if flink_managed_api_key is None:
            flink_managed_api_key = settings.FLINK_MANAGED_API_SECRET
        self.kafka_broker = kafka_broker
        self.window_minutes = window_minutes
        self.output_topic = output_topic
        self.group_id = group_id
        self.job_name = job_name
        self.flink_mode = flink_mode
        self.flink_host = flink_host
        self.flink_port = flink_port
        self.flink_managed_endpoint = flink_managed_endpoint
        self.flink_managed_api_key = flink_managed_api_key
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
        
        Connects to Flink cluster based on configured mode and builds the pipeline.
        
        Returns:
            Configured Flink execution environment
        """
        # Create execution environment based on mode
        self.env = _create_flink_env(
            mode=self.flink_mode,
            host=self.flink_host,
            port=self.flink_port,
            managed_endpoint=self.flink_managed_endpoint,
            managed_api_key=self.flink_managed_api_key
        )
        self.env.set_parallelism(1)
        
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

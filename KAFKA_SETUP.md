# Kafka Implementation Summary

## Overview
Successfully implemented Apache Kafka for event-driven architecture with full Docker integration and service integration.

## Changes Made

### 1. Docker Compose Updates (`docker-compose.yml`)
- **Zookeeper Service**: Added Confluent Zookeeper 7.5.0 for Kafka coordination
  - Port: 2181
  - Healthcheck: Echo ruok command
  - Proper startup dependencies

- **Kafka Service**: Added Confluent Kafka 7.5.0 with full configuration
  - Internal listener: `kafka:29092` (for services inside Docker)
  - External listener: `kafka:9092` (for local connections)
  - Ports: 9092 (client), 9101 (metrics)
  - Auto topic creation enabled
  - Retention: 168 hours (7 days)
  - Dependency: Waits for Zookeeper to be healthy

### 2. Dependencies (`requirements.txt`)
- Added `aiokafka`: Async Kafka producer/consumer library

### 3. Core Kafka Infrastructure

#### Producer Implementation (`libs/events/kafka.py`)
- **KafkaEmitter class**: Full async Kafka producer
  - `start()`: Initialize producer connection
  - `emit_async()`: Primary async event emission method
  - `emit()`: Sync method for backward compatibility (logs warning)
  - `close()`: Graceful shutdown with logging
  - Proper error handling and logging
  - Configurable broker address (default: `kafka:29092`)

- **Global functions**:
  - `set_broker()`: Configure Kafka broker before initialization
  - `get_emitter()`: Singleton pattern for producer instance
  - `emit_event()`: Sync wrapper (for compatibility)
  - `emit_event_async()`: Recommended async method

#### Consumer Implementation (`libs/events/consumer.py`)
- **KafkaConsumer class**: Full async Kafka consumer
  - Topic subscription and handler registration
  - `register_handler()`: Map topics to async/sync handlers
  - `start()`: Initialize consumer connection
  - `consume()`: Indefinite message listening loop
  - `close()`: Graceful shutdown
  - Consumer group support for offset tracking

- **Factory function**:
  - `create_consumer()`: Helper to create and start consumer in one call

### 4. Updated Services

#### Submission Service (`services/submission_service/app/main.py`)
- Added Kafka producer lifecycle management via `lifespan` context manager
- Events emitted to topic: `paper_uploaded`
- Handles both POST endpoints:
  - Direct submission creation
  - File upload workflow
- Async event emission with error handling
- Graceful startup/shutdown of Kafka producer

#### Plagiarism Service (`services/plagiarism_service/app/main.py`)
- Added Kafka producer lifecycle management
- Events emitted to topic: `plagiarism_checked`
- Emits after plagiarism check completes and results are stored in MongoDB
- Async event emission with error handling

#### Analytics Service (`services/analytics_service/app/main.py`)
- Added Kafka consumer with lifespan management
- Subscribes to topics: `paper_uploaded`, `plagiarism_checked`
- Event handlers:
  - `handle_submission_event()`: Increments submission counter
  - `handle_plagiarism_event()`: Collects plagiarism scores (keeps last 100)
- Computes analytics based on collected event data
- Real-time metrics aggregation from events

#### Notification Service (`services/notification_service/app/main.py`)
- Added Kafka consumer with lifespan management
- Subscribes to topics: `paper_uploaded`, `plagiarism_checked`
- Event handlers:
  - `handle_submission_event()`: Notifies user of successful upload
  - `handle_plagiarism_event()`: Notifies user of plagiarism check results
- Creates notifications in database based on events
- Validates users before creating notifications

### 5. Updated Module Exports (`libs/events/__init__.py`)
- Exported `emit_event_async` for async event emission
- Exported `set_broker` for broker configuration
- Exported `KafkaConsumer` for consumer usage
- Exported `create_consumer` factory function

## Event Flow

```
Submission Upload
        ↓
    Submission Service
        ↓
    emit paper_uploaded event
        ↓
    Kafka Topic: paper_uploaded
        ↓
    ├─→ Notification Service (handle_submission_event)
    │        ↓
    │   Create user notification
    │
    └─→ Analytics Service (handle_submission_event)
             ↓
         Increment counter

Plagiarism Check
        ↓
    Plagiarism Service
        ↓
    emit plagiarism_checked event
        ↓
    Kafka Topic: plagiarism_checked
        ↓
    ├─→ Notification Service (handle_plagiarism_event)
    │        ↓
    │   Create user notification
    │
    └─→ Analytics Service (handle_plagiarism_event)
             ↓
         Collect plagiarism score
```

## Configuration

### Environment Variables
Services look for `KAFKA_BROKER` environment variable. Default: `kafka:29092`

Services can override the broker by setting in `settings.py`:
```python
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
```

### Docker Networking
- Internal container communication: Use `kafka:29092`
- Local/external connection: Use `localhost:9092`

## Running the System

### Start all services with Kafka:
```bash
docker-compose up -d
```

### Verify Kafka is running:
```bash
docker-compose logs kafka
docker-compose logs zookeeper
```

### Check Kafka topics:
```bash
docker exec paper-submission-kafka kafka-topics --list --bootstrap-server kafka:29092
```

### Create topics manually (if auto-create disabled):
```bash
docker exec paper-submission-kafka kafka-topics --create --bootstrap-server kafka:29092 \
  --topic paper_uploaded --partitions 1 --replication-factor 1

docker exec paper-submission-kafka kafka-topics --create --bootstrap-server kafka:29092 \
  --topic plagiarism_checked --partitions 1 --replication-factor 1
```

### Monitor messages in real-time:
```bash
docker exec paper-submission-kafka kafka-console-consumer --bootstrap-server kafka:29092 \
  --topic paper_uploaded --from-beginning

docker exec paper-submission-kafka kafka-console-consumer --bootstrap-server kafka:29092 \
  --topic plagiarism_checked --from-beginning
```

## Logging

All Kafka operations are logged with proper levels:
- INFO: Connection established, events sent/received
- WARNING: Compatibility warnings, missing handlers
- ERROR: Connection failures, event processing errors

Check service logs:
```bash
docker-compose logs submission_service
docker-compose logs analytics_service
docker-compose logs notification_service
```

## Error Handling

- Producer startup failures are logged but don't crash the application
- Consumer errors are caught and logged without stopping the consumer loop
- Event emission failures are logged and don't block the request
- Graceful shutdown ensures all connections are properly closed

## Future Enhancements

1. Add topic replicas for high availability
2. Implement consumer group rebalancing strategies
3. Add metrics collection (e.g., Prometheus integration)
4. Implement message compression for better performance
5. Add dead-letter queue for failed event processing
6. Implement retry logic with exponential backoff

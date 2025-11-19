# Kafka Quick Reference

## Key Components

### Docker Containers
- **zookeeper** (port 2181): Kafka coordination & broker management
- **kafka** (ports 9092, 9101): Event broker with auto topic creation enabled

## Service Integration

### Event Producers
| Service | Topic | Event | When Emitted |
|---------|-------|-------|--------------|
| Submission | `paper_uploaded` | New file uploaded | After file saved & submission created |
| Plagiarism | `plagiarism_checked` | Check completed | After plagiarism analysis & stored in DB |

### Event Consumers
| Service | Topics | Handlers |
|---------|--------|----------|
| Analytics | `paper_uploaded`, `plagiarism_checked` | Count submissions, collect plagiarism scores |
| Notification | `paper_uploaded`, `plagiarism_checked` | Create user notifications |

## API Usage

### Emit Event (Producer)
```python
from libs.events import KafkaProducerClient

# Initialize client
kafka_client = KafkaProducerClient(broker="kafka:29092")
await kafka_client.start()

# Emit events
await kafka_client.emit("topic_name", {"key": "value"})

# Cleanup
await kafka_client.close()
```

### Consume Events (Consumer)
```python
from libs.events import KafkaConsumerClient

# Create consumer
kafka_client = KafkaConsumerClient(
    broker="kafka:29092",
    group_id="my-service",
    topics=["topic1", "topic2"]
)

# Register handlers
async def my_handler(event: dict):
    print(f"Received: {event}")

kafka_client.register_handler("topic1", my_handler)

# Start consuming
await kafka_client.start()
await kafka_client.consume()  # Blocks indefinitely
```

### Centralized Logging
```python
from libs.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Service started")
logger.error("An error occurred", exc_info=True)
```

## Docker Commands

### Start services
```bash
docker-compose up -d
```

### List topics
```bash
docker exec paper-submission-kafka kafka-topics --list --bootstrap-server kafka:29092
```

### View messages (from beginning)
```bash
docker exec paper-submission-kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic paper_uploaded \
  --from-beginning
```

### View service logs
```bash
docker-compose logs -f submission_service
docker-compose logs -f plagiarism_service
docker-compose logs -f analytics_service
docker-compose logs -f notification_service
```

## Broker Addresses
- **Internal (Docker-to-Docker)**: `kafka:29092`
- **External (Host/CLI)**: `localhost:9092`

## Configuration
- Auto topic creation: ENABLED
- Retention: 7 days
- Replication factor: 1
- Partitions: 1 (default)

## Event Payloads

### paper_uploaded
```json
{
  "id": "submission-uuid",
  "user_id": "user-uuid",
  "assignment_id": "assignment-uuid",
  "uploaded_at": "2024-11-19T10:30:00Z",
  "file_url": "/uploads/filename.ext",
  "text": "file content (if text file)"
}
```

### plagiarism_checked
```json
{
  "submission_id": "submission-uuid",
  "internal_score": 0.45,
  "external_score": 0.23,
  "ai_generated_probability": 0.12,
  "flagged_sections": ["section1", "section2"]
}
```

## Health Checks
All services have healthchecks enabled. Kafka waits for Zookeeper before starting.

## Troubleshooting

**Kafka won't start:**
- Check if port 9092 is available
- Verify Zookeeper is running: `docker-compose logs zookeeper`
- Check Kafka broker logs: `docker-compose logs kafka`

**Events not appearing:**
- Verify producer/consumer broker addresses match
- Check service logs for connection errors
- Ensure topics are created (auto-create enabled)

**Consumer stuck/not receiving:**
- Check consumer group: `docker exec paper-submission-kafka kafka-consumer-groups --list --bootstrap-server kafka:29092`
- Reset offset if needed: `kafka-consumer-groups --reset-offsets --to-earliest --execute`

**High memory usage:**
- Reduce `KAFKA_LOG_RETENTION_HOURS` (currently 168)
- Scale down partitions/replicas
- Implement message size limits

# Paper Submission Portal

A microservices-based plagiarism detection system for research paper submissions with event-driven architecture and stream processing.

## Architecture

This project follows a **microservices architecture** with embedded stream processing.

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRODUCER SERVICES                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                    ┌──────────────────┐
    │  Submission      │                    │  Plagiarism      │
    │  Service         │                    │  Service         │
    │  (Port 8002)     │                    │  (Port 8003)     │
    │                  │                    │                  │
    │ • Business logic │                    │ • Plagiarism     │
    │ • Validation     │                    │   detection      │
    │ • Persistence    │                    │ • Severity calc  │
    │                  │                    │ • Risk flagging  │
    │ • aiokafka       │                    │ • AI detection   │
    │   stream proc    │                    │                  │
    └────────┬─────────┘                    │ • aiokafka       │
             │                              │   stream proc    │
             │ Produces                     └────────┬─────────┘
             │                                       │
             │                                       │ Produces
             ▼                                       ▼
    ┌────────────────────┐            ┌────────────────────────┐
    │ Kafka Topic:       │            │ Kafka Topic:           │
    │ paper_uploaded     │            │ plagiarism_checked     │
    └────────┬───────────┘            └────────┬───────────────┘
             │                                 │
             │                                 │
┌────────────┼─────────────────────────────────┼─────────────────┐
│            │  EMBEDDED STREAM PROCESSORS     │                 │
│            │  (aiokafka - async)             │                 │
│            │                                 │                 │
│  ┌─────────▼──────────────┐      ┌──────────▼──────────────┐  │
│  │ Submission Service     │      │ Plagiarism Service      │  │
│  │ Stream Processor       │      │ Stream Processor        │  │
│  │                        │      │                         │  │
│  │ • Consume topic        │      │ • Consume topic         │  │
│  │ • Add metadata         │      │ • Add metadata          │  │
│  │ • Text length calc     │      │ • Passthrough enriched  │  │
│  │ • Async processing     │      │   data from service     │  │
│  └──────────┬─────────────┘      └──────────┬──────────────┘  │
│             │                               │                 │
└─────────────┼───────────────────────────────┼─────────────────┘
              │ Writes to                     │ Writes to
              ▼                               ▼
    ┌─────────────────────┐         ┌─────────────────────────┐
    │ Kafka Topic:        │         │ Kafka Topic:            │
    │ paper_uploaded_     │         │ plagiarism_checked_     │
    │ processed           │         │ processed               │
    └─────────┬───────────┘         └─────────┬───────────────┘
              │                               │
              │         ┌─────────────────────┘
              │         │
              └─────────┼─────────┐
                        │         │
┌───────────────────────┼─────────┼───────────────────────────┐
│        ANALYTICS      │         │                           │
│        SERVICE        │         │                           │
│                       ▼         ▼                           │
│            ╔═══════════════════════════╗                    │
│            ║ Flink Stream Processor    ║                    │
│            ║ (Windowed Aggregations)   ║                    │
│            ║                           ║                    │
│            ║ • Reads both topics       ║                    │
│            ║ • 5-min tumbling windows  ║                    │
│            ║ • Union streams           ║                    │
│            ║ • Aggregates metrics:     ║                    │
│            ║   - Submission counts     ║                    │
│            ║   - Avg plagiarism score  ║                    │
│            ║   - High-risk count       ║                    │
│            ║   - AI detection count    ║                    │
│            ║                           ║                    │
│            ║ ⚠️  Flink used ONLY for   ║                    │
│            ║    time-based windowing   ║                    │
│            ║    (unavoidable)          ║                    │
│            ╚═══════════┬═══════════════╝                    │
│                        │                                    │
└────────────────────────┼────────────────────────────────────┘
                         │ Writes aggregated data
                         ▼
                ┌────────────────────┐
                │ Kafka Topic:       │
                │ analytics_window   │
                └────────┬───────────┘
                         │
                         │ Consumed by
                         │ Analytics Service
                         │ (aiokafka)
                         ▼
                ┌────────────────────┐
                │ Analytics Service  │
                │ REST API           │
                │ (Port 8004)        │
                └────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  OTHER CONSUMER SERVICES                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐
│  Notification    │  │  Notification    │
│  Service         │  │  Service         │
│  (Port 8005)     │  │  (Port 8005)     │
│                  │  │                  │
│  Consumes:       │  │  Consumes:       │
│  paper_uploaded_ │  │  plagiarism_     │
│  processed       │  │  checked_        │
│                  │  │  processed       │
│  • Upload alerts │  │  • Smart alerts  │
│  • Text length   │  │    with severity │
│    in notif      │  │  • Risk-based    │
│                  │  │    messages      │
└──────────────────┘  └──────────────────┘
```

### Services

1. **Gateway** (`services/gateway/`) - Port 8000
   - Web frontend and API gateway
   - User interface for students and faculty

2. **User Service** (`services/users_service/`) - Port 8001
   - Manages users (students and faculty)
   - CRUD operations for user accounts

3. **Submission Service** (`services/submission_service/`) - Port 8002
   - Handles research paper submissions
   - **Business logic**: Submission validation, file handling
   - **Stream processor** (aiokafka): Enriches events with metadata
   - Emits to: `paper_uploaded` → `paper_uploaded_processed`

4. **Plagiarism Service** (`services/plagiarism_service/`) - Port 8003
   - **Business logic**: Plagiarism detection, severity categorization, risk flagging, AI detection
   - **Stream processor** (aiokafka): Forwards enriched events
   - Emits to: `plagiarism_checked` → `plagiarism_checked_processed`

5. **Analytics Service** (`services/analytics_service/`) - Port 8004
   - **Business logic**: Analytics queries and trending
   - **Stream processor** (Apache Flink): Time-based windowed aggregations (5-min windows)
   - Consumes: Both processed topics → Produces: `analytics_window`

6. **Notification Service** (`services/notification_service/`) - Port 8005
   - Sends notifications to users
   - Consumes processed topics for smart notifications

### Architecture Principles

#### 1. Business Logic in Services ✅
- ✅ Severity calculation in `plagiarism_service/app/engine.py`
- ✅ Risk flagging in `plagiarism_service/app/engine.py`
- ✅ AI detection in `plagiarism_service/app/engine.py`
- ✅ Single source of truth for domain logic

#### 2. Async Stream Processing (aiokafka) ✅
- ✅ Submission service: Simple consume → enrich → produce
- ✅ Plagiarism service: Simple passthrough with metadata
- ✅ No blocking operations, fully async

#### 3. Flink ONLY for Time Windowing ⚠️
- ✅ Analytics service: 5-minute tumbling windows
- ✅ Event time processing with watermarks
- ✅ State management for window aggregations
- ❌ NOT used for business logic
- ❌ NOT used for simple consume/produce

#### 4. Separation of Concerns
**Services own:**
- Domain logic
- Data validation
- API endpoints
- Persistence

**Stream processors own:**
- Kafka consumption/production
- Minimal enrichment (metadata)
- Time-based aggregations (Flink only)

### Kafka Topics

| Topic | Producer | Consumer |
|-------|----------|----------|
| `paper_uploaded` | submission-service | submission stream processor |
| `paper_uploaded_processed` | submission stream processor | notification-service, analytics Flink |
| `plagiarism_checked` | plagiarism-service | plagiarism stream processor |
| `plagiarism_checked_processed` | plagiarism stream processor | notification-service, analytics Flink |
| `analytics_window` | analytics Flink processor | analytics-service |

### Technology Choices

| Component | Technology | Justification |
|-----------|------------|---------------|
| Submission enrichment | aiokafka | Simple async consume/produce |
| Plagiarism passthrough | aiokafka | Simple async consume/produce |
| Analytics windowing | Apache Flink | Time-based windows unavoidable |
| Business logic | FastAPI services | Domain expertise in services |
| Event schema | Pydantic | Type safety and validation |

### Shared Libraries

- **libs/events/** - Event schemas and Kafka utilities
  - Pydantic models for inter-service communication
  - Async Kafka producer/consumer clients (aiokafka)

- **config/** - Centralized configuration
  - Environment-based settings
  - Service URLs and Kafka configuration

## Project Structure

```
Project/
├── services/                           # Microservices
│   ├── gateway/                        # Web UI (Port 8000)
│   ├── users_service/                  # User management (Port 8001)
│   ├── submission_service/             # Paper submissions (Port 8002)
│   │   └── app/
│   │       ├── main.py                 # FastAPI app
│   │       ├── stream_processor.py     # aiokafka stream processor
│   │       └── store.py                # Data layer
│   ├── plagiarism_service/             # Plagiarism detection (Port 8003)
│   │   └── app/
│   │       ├── main.py                 # FastAPI app
│   │       ├── engine.py               # Business logic (severity, risk, AI)
│   │       ├── stream_processor.py     # aiokafka stream processor
│   │       └── store.py                # Data layer
│   ├── analytics_service/              # Analytics (Port 8004)
│   │   └── app/
│   │       ├── main.py                 # FastAPI app
│   │       ├── stream_processor.py     # Flink windowed aggregations
│   │       └── store.py                # Data layer
│   └── notification_service/           # Notifications (Port 8005)
├── libs/                               # Shared libraries
│   └── events/
│       ├── schemas.py                  # Pydantic event models
│       └── kafka.py                    # Async Kafka clients
├── config/                             # Configuration
│   ├── settings.py                     # Centralized settings
│   └── logging.py                      # Logging setup
├── scripts/                            # Utility scripts
│   ├── seed_data.py                    # Seed test data
│   └── test_workflow.py                # Test end-to-end flow
├── k8s/                                # Kubernetes manifests
├── ARCHITECTURE.txt                    # Data flow diagram
└── requirements.txt                    # Python dependencies
```

## Setup

### Prerequisites

- Python 3.12+
- Virtual environment (recommended)

### Installation

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running Services

Each service can be run independently:

```bash
# User Service
uvicorn services.users_service.app.main:app --port 8001

# Submission Service
uvicorn services.submission_service.app.main:app --port 8002

# Plagiarism Service
uvicorn services.plagiarism_service.app.main:app --port 8003

# Analytics Service
uvicorn services.analytics_service.app.main:app --port 8004

# Notification Service
uvicorn services.notification_service.app.main:app --port 8005

# Gateway (Web UI)
uvicorn services.gateway.app.main:app --port 8000
```

### Running Tests

```bash
# Run all tests
pytest -q

# Run specific service tests
pytest services/users_service/tests/ -v
pytest services/submission_service/tests/ -v
```

## Configuration

Environment variables can be set in a `.env` file at the project root:

```env
# Service URLs
USERS_SERVICE_URL=http://localhost:8001
SUBMISSION_SERVICE_URL=http://localhost:8002
PLAGIARISM_SERVICE_URL=http://localhost:8003
ANALYTICS_SERVICE_URL=http://localhost:8004
NOTIFICATION_SERVICE_URL=http://localhost:8005
GATEWAY_URL=http://localhost:8000

# Kafka
KAFKA_BROKER=localhost:9092

# Flink
FLINK_JOBMANAGER=http://localhost:8081

# Security
SECRET_KEY=your-secret-key-here
```

## Event-Driven Architecture

Services communicate via Kafka topics with embedded stream processors.

### Kafka Topics Flow

```
submission_service
    │
    ├─> paper_uploaded (raw)
    │       │
    │       ├─> [submission stream processor - aiokafka]
    │       │       • Adds metadata (processed_at, text_length)
    │       │
    │       └─> paper_uploaded_processed
    │               │
    │               └─> notification_service (consumes)
    │               └─> analytics Flink processor (consumes)

plagiarism_service
    │
    ├─> plagiarism_checked (raw, enriched by service)
    │       • severity: high/medium/low
    │       • requires_review: boolean
    │       • ai_generated_likely: boolean
    │       │
    │       ├─> [plagiarism stream processor - aiokafka]
    │       │       • Adds processing metadata
    │       │
    │       └─> plagiarism_checked_processed
    │               │
    │               └─> notification_service (consumes)
    │               └─> analytics Flink processor (consumes)

analytics_service
    │
    ├─> [Flink stream processor]
    │       • Reads: paper_uploaded_processed + plagiarism_checked_processed
    │       • 5-minute tumbling windows
    │       • Aggregates: counts, averages, high-risk counts
    │
    └─> analytics_window
            │
            └─> analytics_service REST API (consumes)
```

### Why Different Technologies?

| Service | Stream Tech | Justification |
|---------|-------------|---------------|
| Submission | aiokafka | Simple consume → enrich → produce |
| Plagiarism | aiokafka | Simple passthrough (logic in service) |
| Analytics | Apache Flink | Time-based windowing requires specialized infrastructure |

**Flink is used ONLY in analytics service** because implementing proper time-based windowing, watermarks, state management, and late data handling manually would be overly complex.

## API Endpoints

### Gateway (Port 8000)
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login handler
- `GET /dashboard/student` - Student dashboard
- `GET /dashboard/faculty` - Faculty dashboard

### User Service (Port 8001)
- `POST /users` - Create user
- `GET /users/{id}` - Get user by ID
- `GET /users` - List all users
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

### Submission Service (Port 8002)
- `POST /submissions` - Create paper submission
- `GET /submissions/{id}` - Get paper submission
- `GET /submissions/user/{user_id}` - Get user's paper submissions

### Plagiarism Service (Port 8003)
- `POST /check` - Check research paper for plagiarism
- `GET /results/{submission_id}` - Get plagiarism results
- `GET /stats` - Get plagiarism statistics

**Returns enriched plagiarism results with:**
- `severity`: "low" | "medium" | "high" (calculated in `engine.py`)
- `requires_review`: boolean (true if internal_score >= 0.5)
- `ai_generated_likely`: boolean (true if ai_probability >= 0.7)

### Analytics Service (Port 8004)
- `GET /analytics/latest` - Get latest analytics window
- `GET /analytics/history` - Get analytics history

### Notification Service (Port 8005)
- `POST /notify` - Send notification

## Development

### Adding a New Service

1. Create service directory under `services/`
2. Add `app/main.py` with FastAPI app and lifespan management
3. If consuming Kafka, add `app/stream_processor.py` (use aiokafka for simple cases)
4. Add business logic in domain modules (e.g., `engine.py`, `store.py`)
5. Add tests in `tests/`
6. Import from `libs.events` for shared schemas

### Best Practices

- ✅ **Business logic in services** - Keep domain logic in service code, not stream processors
- ✅ **Use aiokafka first** - Only use Flink if you need time-based windowing
- ✅ **Event schemas** - Use Pydantic models from `libs.events.schemas`
- ✅ **Async everywhere** - Use async/await for all I/O operations
- ✅ **Loose coupling** - Services communicate via events, not direct HTTP calls
- ✅ **Test independently** - Each service should be testable in isolation

### Stream Processing Guidelines

**When to use aiokafka:**
- Simple consume → process → produce patterns
- Stateless transformations
- Metadata enrichment

**When to use Flink:**
- Time-based windowing (tumbling, sliding, session windows)
- Complex event processing with state
- Event time processing with watermarks
- When you need exactly-once semantics with state

## Kubernetes Deployment

Kubernetes manifests are provided in `k8s/`:

```bash
# Deploy all services
kubectl apply -f k8s/base/
kubectl apply -f k8s/gateway/
kubectl apply -f k8s/users-service/
kubectl apply -f k8s/submission-service/
kubectl apply -f k8s/plagiarism-service/
kubectl apply -f k8s/analytics-service/
kubectl apply -f k8s/notification-service/

# Or use the deployment script
bash deploy-k8s.sh
```

## Important Notes

### Why aiokafka Instead of Flink for Most Services?

**aiokafka is preferred because:**
- ✅ Fully async/await compatible (non-blocking)
- ✅ Simple consume → process → produce patterns
- ✅ Lower resource overhead
- ✅ Easier to test and debug
- ✅ No complex infrastructure needed

**Flink is ONLY used when:**
- ⚠️ Time-based windowing is required (tumbling, sliding, session windows)
- ⚠️ Event time processing with watermarks is needed
- ⚠️ Stateful aggregations across time windows
- ⚠️ Complex event processing (CEP) patterns

### Business Logic Placement

**❌ WRONG:**
```python
# DON'T put business logic in stream processors
class MyStreamProcessor:
    def process(self, event):
        if event['score'] > 0.7:  # ❌ Business logic
            event['severity'] = 'high'
```

**✅ CORRECT:**
```python
# services/plagiarism_service/app/engine.py
async def run_plagiarism_pipeline(sub: Submission) -> PlagiarismResult:
    internal = check_internal_plagiarism()
    
    # ✅ Business logic in service
    if internal >= 0.7:
        severity = "high"
    elif internal >= 0.4:
        severity = "medium"
    else:
        severity = "low"
    
    return PlagiarismResult(..., severity=severity)
```

### Stream Processor Template

**For simple consume/produce (use aiokafka):**
```python
# services/my_service/app/stream_processor.py
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

class MyStreamProcessor:
    async def process_messages(self):
        async for msg in self.consumer:
            event = json.loads(msg.value)
            # ✅ Minimal enrichment only
            event['processed_at'] = datetime.utcnow().isoformat()
            await self.producer.send('output_topic', json.dumps(event).encode())
```

**For time-based windowing (use Flink):**
```python
# services/analytics_service/app/stream_processor.py
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common import Time

# ✅ Flink for windowing
stream.window(TumblingProcessingTimeWindows.of(Time.minutes(5))) \
      .aggregate(MyAggregator())
```

## Technology Stack

### Core
- **FastAPI** - Web framework for microservices
- **Pydantic** - Data validation and event schemas
- **aiokafka** - Async Kafka client for stream processing
- **Apache Flink** - Time-based windowing (analytics only)
- **Uvicorn** - ASGI server

### Infrastructure
- **Apache Kafka** - Event streaming platform
- **PostgreSQL** - Relational database (users, submissions)
- **MongoDB** - Document database (plagiarism results)
- **Redis** - In-memory cache (analytics, notifications)

### Development
- **Pytest** - Testing framework
- **Jinja2** - Template engine (gateway)
- **Docker** - Containerization
- **Kubernetes** - Orchestration (k8s manifests included)

## Docker Deployment

The project includes a complete Docker Compose setup:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down
```

**Infrastructure services included:**
- PostgreSQL (Port 5432)
- MongoDB (Port 27017)
- Redis (Port 6379)
- Zookeeper (Port 2181)
- Kafka (Port 9092)

**Application services:**
- All 6 microservices with embedded stream processors
- Stream processors start automatically with their parent services

### Monitoring

Check service health:
```bash
# Check all services
docker-compose ps

# View specific service logs
docker-compose logs -f analytics_service
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8000 | Web UI and API gateway |
| User Service | 8001 | User management |
| Submission Service | 8002 | Paper submissions + stream processor |
| Plagiarism Service | 8003 | Plagiarism detection + stream processor |
| Analytics Service | 8004 | Analytics + Flink windowing |
| Notification Service | 8005 | Notifications |
| PostgreSQL | 5432 | Relational database |
| MongoDB | 27017 | Document database |
| Redis | 6379 | Cache |
| Zookeeper | 2181 | Kafka coordination |
| Kafka | 9092 | Event streaming |

## Future Enhancements

- [ ] Authentication/authorization (JWT-based)
- [ ] API versioning
- [ ] Health check endpoints for all services
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Monitoring and alerting (Prometheus + Grafana)
- [ ] CI/CD pipeline
- [ ] Advanced Flink features (complex event processing patterns, session windows)
- [ ] ML model integration for plagiarism detection
- [ ] Real-time plagiarism score updates via WebSocket

---

**Complete architecture diagram available above** ⬆️

# Project Submission Portal

A microservices-based plagiarism detection system for academic submissions.

## Architecture

This project follows a **microservices architecture** with the following services:

### Services

1. **User Service** (`services/user_service/`) - Port 8001
   - Manages users (students and faculty)
   - CRUD operations for user accounts

2. **Submission Service** (`services/submission_service/`) - Port 8002
   - Handles assignment submissions
   - Emits submission events to Kafka

3. **Plagiarism Service** (`services/plagiarism_service/`) - Port 8003
   - Detects plagiarism (internal/external)
   - AI-generated content detection
   - Emits plagiarism check results

4. **Analytics Service** (`services/analytics_service/`) - Port 8004
   - Provides submission and plagiarism analytics
   - Tracks trends and spikes

5. **Notification Service** (`services/notification_service/`) - Port 8005
   - Sends notifications to users

6. **Gateway** (`services/gateway/`) - Port 8000
   - Web frontend and API gateway
   - User interface for students and faculty

### Shared Libraries

- **libs/events/** - Event schemas and Kafka utilities
  - Pydantic models for inter-service communication
  - Kafka event emitter (currently stubbed)

- **config/** - Centralized configuration
  - Environment-based settings
  - Service URLs and Kafka configuration

## Project Structure

```
Project/
├── services/                    # All microservices
│   ├── user_service/
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app
│   │   │   └── store.py        # Data layer
│   │   └── tests/
│   ├── submission_service/
│   ├── plagiarism_service/
│   ├── analytics_service/
│   ├── notification_service/
│   └── gateway/
├── libs/                        # Shared libraries
│   └── events/
│       ├── schemas.py          # Pydantic models
│       └── kafka.py            # Event emitter
├── config/                      # Configuration
│   └── settings.py             # Centralized settings
└── requirements.txt
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
uvicorn services.user_service.app.main:app --port 8001

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
pytest services/user_service/tests/ -v
pytest services/submission_service/tests/ -v
```

## Configuration

Environment variables can be set in a `.env` file at the project root:

```env
# Service URLs
USER_SERVICE_URL=http://localhost:8001
SUBMISSION_SERVICE_URL=http://localhost:8002
PLAGIARISM_SERVICE_URL=http://localhost:8003
ANALYTICS_SERVICE_URL=http://localhost:8004
NOTIFICATION_SERVICE_URL=http://localhost:8005
GATEWAY_URL=http://localhost:8000

# Kafka
KAFKA_BROKER=localhost:9092

# Security
SECRET_KEY=your-secret-key-here
```

## Event-Driven Communication

Services communicate via Kafka events:

- **submission_uploaded** - Emitted when a new submission is created
- **plagiarism_checked** - Emitted after plagiarism check completes

*Note: Kafka integration is currently stubbed. To enable real Kafka, update `libs/events/kafka.py` to use `confluent-kafka` or `aiokafka`.*

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
- `POST /submissions` - Create submission
- `GET /submissions/{id}` - Get submission
- `GET /submissions/user/{user_id}` - Get user's submissions

### Plagiarism Service (Port 8003)
- `POST /check` - Check submission for plagiarism

### Analytics Service (Port 8004)
- `GET /analytics/latest` - Get latest analytics window
- `GET /analytics/history` - Get analytics history

### Notification Service (Port 8005)
- `POST /notify` - Send notification

## Development

### Adding a New Service

1. Create service directory under `services/`
2. Add `app/main.py` with FastAPI app
3. Add tests in `tests/`
4. Update `conftest.py` to set correct Python path
5. Import from `libs.events` for shared schemas

### Best Practices

- Each service is independently deployable
- Use shared schemas from `libs.events`
- Emit events for cross-service communication
- Keep services loosely coupled
- Write tests for all endpoints

## Technology Stack

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Pytest** - Testing framework
- **Jinja2** - Template engine (Gateway)
- **Uvicorn** - ASGI server

## Future Enhancements

- [ ] Implement real Kafka producer/consumer
- [ ] Add Docker Compose for orchestration
- [ ] Implement authentication/authorization
- [ ] Add database persistence (SQLAlchemy/PostgreSQL)
- [ ] Add API versioning
- [ ] Implement health check endpoints
- [ ] Add monitoring and logging (Prometheus, Grafana)
- [ ] CI/CD pipeline

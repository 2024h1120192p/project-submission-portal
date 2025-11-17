# Project Structure Overview

This document explains the reorganized microservices structure.

## New Structure

```
Project/
├── .env.example              # Example environment variables
├── README.md                 # Main documentation
├── requirements.txt          # Python dependencies
├── run_all_services.sh       # Script to run all services
│
├── config/                   # 🆕 Centralized configuration
│   ├── __init__.py
│   └── settings.py           # Environment-based settings
│
├── libs/                     # Shared libraries
│   ├── __init__.py
│   └── events/               # Event schemas and Kafka
│       ├── __init__.py
│       ├── schemas.py        # Pydantic models
│       └── kafka.py          # 🆕 Kafka event emitter
│
├── services/                 # 🆕 All microservices grouped here
│   ├── __init__.py
│   │
│   ├── user_service/
│   │   ├── __init__.py       # 🆕 Service entry point
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py       # FastAPI app
│   │   │   └── store.py      # Data layer
│   │   └── tests/
│   │       ├── conftest.py   # ✏️ Updated Python path
│   │       └── test_users.py # ✏️ Updated imports
│   │
│   ├── submission_service/
│   │   ├── __init__.py       # 🆕
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py       # ✏️ Uses libs.events.kafka
│   │   │   └── store.py
│   │   └── tests/
│   │       ├── conftest.py   # ✏️ Updated
│   │       └── test_submissions.py  # ✏️ Updated
│   │
│   ├── plagiarism_service/
│   │   ├── __init__.py       # 🆕
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py       # ✏️ Uses libs.events.kafka
│   │   │   └── engine.py
│   │   └── tests/
│   │       ├── conftest.py   # ✏️ Updated
│   │       └── test_plagarism.py  # ✏️ Updated
│   │
│   ├── analytics_service/
│   │   ├── __init__.py       # 🆕
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── store.py
│   │   └── tests/
│   │       ├── conftest.py   # ✏️ Updated
│   │       └── test_analytics.py  # ✏️ Updated
│   │
│   ├── notification_service/
│   │   ├── __init__.py       # 🆕
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── store.py
│   │   └── tests/
│   │       ├── conftest.py   # ✏️ Updated
│   │       └── test_notification.py  # ✏️ Updated
│   │
│   └── gateway/
│       ├── __init__.py       # 🆕
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py       # ✏️ Updated template/static paths
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── routes_public.py      # ✏️ Updated template path
│       │   │   └── routes_dashboard.py   # ✏️ Updated template path
│       │   ├── core/
│       │   │   ├── __init__.py
│       │   │   └── config.py
│       │   ├── static/
│       │   │   ├── css/
│       │   │   └── js/
│       │   └── templates/
│       │       ├── base.html
│       │       ├── index.html
│       │       ├── login.html
│       │       ├── dashboard_student.html
│       │       └── dashboard_faculty.html
│       └── tests/
│           ├── conftest.py   # ✏️ Updated
│           └── test_gateway.py  # ✏️ Updated
│
└── tests/                    # Root-level integration tests (empty)
```

## Key Changes

### Legend
- 🆕 = New file/directory
- ✏️ = Modified file

### 1. Services Grouped Under `services/`

**Before:**
```
Project/
├── user_service/
├── submission_service/
├── plagiarism_service/
├── analytics_service/
├── notification_service/
├── gateway/
└── libs/
```

**After:**
```
Project/
├── services/          # All services grouped
│   ├── user_service/
│   ├── submission_service/
│   ├── plagiarism_service/
│   ├── analytics_service/
│   ├── notification_service/
│   └── gateway/
├── libs/              # Shared libraries
└── config/            # Centralized config
```

### 2. Import Changes

**Before:**
```python
from user_service.app.main import app
from libs.events.schemas import User
```

**After:**
```python
from services.user_service.app.main import app
from libs.events.schemas import User
from libs.events.kafka import emit_event
```

### 3. Enhanced libs/events Module

**New files:**
- `libs/events/kafka.py` - Kafka event emitter utility
- `libs/events/__init__.py` - Exports all schemas and utilities

**Usage:**
```python
from libs.events import emit_event, User, Submission

# Emit event
emit_event("submission_uploaded", submission.model_dump())
```

### 4. Centralized Configuration

**New module: `config/`**
```python
from config import get_settings

settings = get_settings()
kafka_broker = settings.KAFKA_BROKER
```

### 5. Service Entry Points

Each service now has a top-level `__init__.py` that exports the app:

```python
# services/user_service/__init__.py
from .app.main import app
__all__ = ["app"]
```

### 6. Test Configuration Updates

All `conftest.py` files updated to reference the correct root:

**Before:**
```python
ROOT = os.path.join(os.path.dirname(__file__), "../../")
```

**After:**
```python
ROOT = os.path.join(os.path.dirname(__file__), "../../../")
```

### 7. Gateway Path Updates

Template and static file paths updated:

**Before:**
```python
StaticFiles(directory="gateway/app/static")
Jinja2Templates(directory="gateway/app/templates")
```

**After:**
```python
StaticFiles(directory="services/gateway/app/static")
Jinja2Templates(directory="services/gateway/app/templates")
```

## Benefits

✅ **Better Organization**
- Clear separation between services, libraries, and configuration
- Easier to navigate the codebase

✅ **Consistent Patterns**
- All services follow the same structure
- Standardized imports across the project

✅ **Improved Maintainability**
- Centralized configuration reduces duplication
- Shared Kafka utilities in one place

✅ **Production Ready**
- Better structure for Docker/Kubernetes deployment
- Clear service boundaries

✅ **Still Microservices**
- Each service remains independently deployable
- Services communicate via events
- Loosely coupled architecture

## Migration Notes

If you have scripts or deployment configs referencing old paths, update them:

- `user_service.app.main:app` → `services.user_service.app.main:app`
- `gateway/app/static` → `services/gateway/app/static`

## Running the Project

All functionality remains the same:

```bash
# Run individual services
uvicorn services.user_service.app.main:app --port 8001

# Run all services
./run_all_services.sh

# Run tests
pytest -v
```

## Verification

All 8 tests pass successfully:
```
✓ services/analytics_service/tests/test_analytics.py::test_latest_and_history
✓ services/gateway/tests/test_gateway.py::test_home
✓ services/gateway/tests/test_gateway.py::test_login_post
✓ services/gateway/tests/test_gateway.py::test_dashboards
✓ services/notification_service/tests/test_notification.py::test_notify
✓ services/plagiarism_service/tests/test_plagarism.py::test_check
✓ services/submission_service/tests/test_submissions.py::test_create_and_get
✓ services/user_service/tests/test_users.py::test_create_get_user
```

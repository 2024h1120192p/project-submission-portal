# Service Client Usage Guide

## Overview

This is a **monorepo** where all services are executed from the project root for the paper submission portal. Services should import existing client modules instead of creating duplicate client classes.

## Client Locations

Each service has a `client.py` module that other services can import:

```
services/
├── users_service/app/client.py          → UserServiceClient
├── submission_service/app/client.py     → SubmissionServiceClient
├── plagiarism_service/app/client.py     → PlagiarismServiceClient
├── analytics_service/app/client.py      → AnalyticsServiceClient
└── notification_service/app/client.py   → NotificationServiceClient
```

## How to Use Clients

### ✅ Correct Usage (Import from other services)

```python
# In plagiarism_service/app/main.py
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from config.settings import get_settings

settings = get_settings()

user_service_client = UserServiceClient(settings.USERS_SERVICE_URL)
submission_service_client = SubmissionServiceClient(settings.SUBMISSION_SERVICE_URL)

# Use the clients
user = await user_service_client.get_user(user_id)
submission = await submission_service_client.get(submission_id)
```

### ❌ Incorrect Usage (Creating duplicate classes)

```python
# DON'T DO THIS - Creating duplicate client class
class SubmissionServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        # ... duplicate implementation
```

## Client Methods

### UserServiceClient

Located: `services/users_service/app/client.py`

```python
from services.users_service.app.client import UserServiceClient

client = UserServiceClient("http://localhost:8001")

# Available methods
user = await client.get_user(user_id)        # Get user by ID
users = await client.get_all_users()         # Get all users
# ... more methods available
```

### SubmissionServiceClient

Located: `services/submission_service/app/client.py`

```python
from services.submission_service.app.client import SubmissionServiceClient

client = SubmissionServiceClient("http://localhost:8002")

# Available methods
submission = await client.get(submission_id)              # Get by ID
submissions = await client.list_by_user(user_id)          # Get user's submissions
created = await client.create(submission_obj)             # Create new submission
await client.close()                                       # Close connection
```

### PlagiarismServiceClient

Located: `services/plagiarism_service/app/client.py`

```python
from services.plagiarism_service.app.client import PlagiarismServiceClient

client = PlagiarismServiceClient("http://localhost:8003")

# Available methods
result = await client.check(submission_obj)    # Run plagiarism check
await client.close()                           # Close connection
```

### AnalyticsServiceClient

Located: `services/analytics_service/app/client.py`

```python
from services.analytics_service.app.client import AnalyticsServiceClient

client = AnalyticsServiceClient("http://localhost:8004")

# Available methods
latest = await client.get_latest()                    # Get latest analytics window
history = await client.get_history()                  # Get all analytics history
window = await client.compute_analytics()             # Trigger computation
await client.close()                                  # Close connection
```

### NotificationServiceClient

Located: `services/notification_service/app/client.py`

```python
from services.notification_service.app.client import NotificationServiceClient

client = NotificationServiceClient("http://localhost:8005")

# Available methods
notif = await client.send(user_id, message)                # Send notification
notifs = await client.get_user_notifications(user_id)      # Get user's notifications
all_notifs = await client.get_all_notifications()          # Get all notifications
await client.close()                                       # Close connection
```

## Gateway Service Example

The gateway aggregates all clients:

```python
# services/gateway/app/main.py
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from services.plagiarism_service.app.client import PlagiarismServiceClient
from services.analytics_service.app.client import AnalyticsServiceClient
from services.notification_service.app.client import NotificationServiceClient

class ServiceClients:
    """Container for all microservice clients."""
    
    def __init__(self):
        self.user = UserServiceClient(USER_URL)
        self.submission = SubmissionServiceClient(SUB_URL)
        self.plagiarism = PlagiarismServiceClient(PLAG_URL)
        self.analytics = AnalyticsServiceClient(ANALYTICS_URL)
        self.notification = NotificationServiceClient(NOTIFY_URL)
    
    async def close_all(self):
        """Close all client connections."""
        await self.user.client.close()
        await self.submission.close()
        await self.plagiarism.close()
        await self.analytics.close()
        await self.notification.close()
```

## Service URLs from Config

Always use the centralized config:

```python
from config.settings import get_settings

settings = get_settings()

# Available URLs
settings.USERS_SERVICE_URL          # http://localhost:8001
settings.SUBMISSION_SERVICE_URL     # http://localhost:8002
settings.PLAGIARISM_SERVICE_URL     # http://localhost:8003
settings.ANALYTICS_SERVICE_URL      # http://localhost:8004
settings.NOTIFICATION_SERVICE_URL   # http://localhost:8005
settings.GATEWAY_URL                # http://localhost:8000
```

## Why This Pattern?

### Benefits of Shared Clients

✅ **Single Source of Truth**: One implementation per service
✅ **DRY Principle**: Don't Repeat Yourself
✅ **Easy Maintenance**: Fix once, works everywhere
✅ **Consistent Interface**: Same methods across services
✅ **Type Safety**: Shared types from `libs.events.schemas`
✅ **Monorepo Advantage**: Can import directly between services

### Monorepo Execution

Services are started from project root:
```bash
# From project root
uvicorn services.users_service.app.main:app --port 8001
uvicorn services.submission_service.app.main:app --port 8002
# etc...
```

This means all services can import from each other:
```python
from services.users_service.app.client import UserServiceClient  # ✅ Works!
```

## Common Patterns

### Pattern 1: Service calls another service

```python
# In plagiarism_service/app/main.py
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient

# Initialize
user_client = UserServiceClient(settings.USERS_SERVICE_URL)
sub_client = SubmissionServiceClient(settings.SUBMISSION_SERVICE_URL)

# Use
user = await user_client.get_user(user_id)
submission = await sub_client.get(submission_id)
```

### Pattern 2: Gateway aggregates all services

```python
# In gateway/app/main.py - Create container
class ServiceClients:
    def __init__(self):
        self.user = UserServiceClient(USER_URL)
        self.submission = SubmissionServiceClient(SUB_URL)
        # ... etc

# In gateway/app/api/routes_submissions.py - Use via request.state
clients = request.state.clients
user = await clients.user.get_user(user_id)
submission = await clients.submission.create(sub)
result = await clients.plagiarism.check(sub)
```

### Pattern 3: Client lifecycle management

```python
# Initialize at startup
@app.on_event("startup")
async def startup():
    global client
    client = UserServiceClient(settings.USERS_SERVICE_URL)

# Close on shutdown
@app.on_event("shutdown")
async def shutdown():
    await client.client.close()
```

## Testing with Clients

When testing, import the same clients:

```python
# In tests
from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient

# Use in tests
user_client = UserServiceClient("http://localhost:8001")
user = await user_client.get_user("test_user_id")
assert user is not None
```

## Summary

✅ **Always import** existing client modules from other services
✅ **Never duplicate** client class implementations
✅ **Use centralized config** for service URLs
✅ **Execute from root** to enable cross-service imports
✅ **Close connections** properly on shutdown

This pattern leverages the monorepo structure for clean, maintainable, and DRY code.

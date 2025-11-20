# Configuration System

This project uses a centralized configuration system based on environment variables. All configuration is managed through the `config/` folder and can be customized via a `.env` file in the project root.

## Overview

### Architecture

```
.env (root) → config/settings.py → All Services & Libraries
```

All services and libraries import from `config.settings` rather than hardcoding values. This ensures:
- Single source of truth for all configuration
- Easy environment-specific customization
- Proper defaults for development
- Production-ready configuration management

## Configuration Files

### `config/settings.py`
Central settings module using Pydantic for validation and type safety. Automatically loads from `.env` file.

**Key Features:**
- Type validation with Pydantic
- Automatic `.env` file loading
- Computed properties (e.g., `POSTGRES_URL`, `MONGO_URL`)
- Default values for development
- Cached settings instance via `get_settings()`

### `config/logging.py`
Centralized logging configuration for consistent log formatting across all services.

### `.env` (Root Directory)
Environment-specific configuration file. **Never commit this file to version control.**

### `.env.example` (Root Directory)
Template file showing all available configuration options with example values. Safe to commit.

## Environment Variables

### Service URLs
Configure microservice endpoints:
```env
USERS_SERVICE_URL=http://localhost:8001
SUBMISSION_SERVICE_URL=http://localhost:8002
PLAGIARISM_SERVICE_URL=http://localhost:8003
ANALYTICS_SERVICE_URL=http://localhost:8004
NOTIFICATION_SERVICE_URL=http://localhost:8005
GATEWAY_URL=http://localhost:8000
```

### Kafka Configuration
Message broker settings:
```env
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC_SUBMISSION_UPLOADED=paper_uploaded
KAFKA_TOPIC_PLAGIARISM_CHECKED=plagiarism_checked
```

### Database Configuration

**PostgreSQL** (Users and Submissions):
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=paper_portal
```

**MongoDB** (Plagiarism Results):
```env
MONGO_USER=admin
MONGO_PASSWORD=admin123
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=plagiarism_db
```

**Redis** (Caching/Analytics):
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Flink Configuration
Stream processing engine settings:

```env
# Execution mode: "local", "remote", or "managed"
FLINK_MODE=local

# For REMOTE mode (self-hosted cluster)
FLINK_JOBMANAGER_HOST=flink-jobmanager
FLINK_JOBMANAGER_PORT=8081

# For MANAGED mode (cloud services)
FLINK_MANAGED_ENDPOINT=https://your-flink-cluster.cloud
FLINK_MANAGED_API_KEY=your_api_key
FLINK_MANAGED_API_SECRET=your_api_secret
```

**Modes:**
- `local`: Embedded mini-cluster (development only, not production-ready)
- `remote`: Self-hosted Flink cluster (Docker/Kubernetes)
- `managed`: Fully managed service (AWS Kinesis, Confluent Cloud, etc.)

### Security
```env
SECRET_KEY=your-secret-key-for-jwt-tokens
```

### File Uploads
```env
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
```

## Usage in Code

### In Services

```python
from config.settings import get_settings

settings = get_settings()

# Use settings throughout your code
kafka_client = KafkaProducerClient(broker=settings.KAFKA_BROKER)
user_client = UserServiceClient(settings.USERS_SERVICE_URL)
```

### In Libraries

Libraries automatically use settings as defaults:

```python
from libs.kafka.client import KafkaProducerClient

# Uses settings.KAFKA_BROKER as default
producer = KafkaProducerClient()

# Or override explicitly
producer = KafkaProducerClient(broker="custom-broker:9092")
```

## Docker Compose

The `docker-compose.yml` file is configured to read from `.env`:

```yaml
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-admin123}
      # ...
```

This ensures Docker containers use the same configuration as local services.

## Deployment Environments

### Development (Local)
1. Copy `.env.example` to `.env`
2. Keep defaults or customize as needed
3. Run services locally: `./run_all_services.sh`

### Docker Compose
1. Ensure `.env` exists with appropriate values
2. Run: `docker-compose up`
3. Services automatically use environment variables

### Kubernetes
Environment variables are configured via:
- `k8s/base/configmap.yaml` - Non-sensitive configuration
- `k8s/base/secrets.yaml` - Sensitive data (base64 encoded)

Services load these via deployment manifests.

### Production
**Security Best Practices:**
1. Never commit `.env` to version control
2. Use strong, unique values for all passwords and secrets
3. Change `SECRET_KEY` to a cryptographically secure random value
4. Consider using secret management services (AWS Secrets Manager, HashiCorp Vault, etc.)
5. Use `managed` Flink mode for production workloads
6. Enable TLS/SSL for all database connections
7. Restrict network access using security groups/firewalls

## Configuration Validation

The `Settings` class uses Pydantic for automatic validation:

```python
class Settings(BaseSettings):
    POSTGRES_PORT: int = 5432  # Type-checked
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    # Computed properties
    @property
    def POSTGRES_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:..."
```

Invalid types or missing required fields will raise clear errors on startup.

## Troubleshooting

### Services can't find configuration
**Problem:** `ModuleNotFoundError: No module named 'config'`

**Solution:** Ensure you're running from the project root and the `config/` directory is in your Python path.

### Environment variables not loading
**Problem:** Changes to `.env` not reflected in services

**Solution:**
1. Restart the service (settings are loaded on startup)
2. Check `.env` file is in project root
3. Ensure no syntax errors in `.env` (no spaces around `=`)
4. Check `model_config` in `Settings` class includes `env_file=".env"`

### Default values used instead of .env values
**Problem:** `.env` values ignored

**Solution:**
1. Check variable names match exactly (case-sensitive)
2. Ensure `.env` file is named correctly (not `.env.txt`)
3. Look for `case_sensitive=True` in settings config

## Adding New Configuration

To add a new configuration variable:

1. **Add to `config/settings.py`:**
   ```python
   class Settings(BaseSettings):
       NEW_CONFIG: str = "default_value"
   ```

2. **Add to `.env.example`:**
   ```env
   NEW_CONFIG=example_value
   ```

3. **Update `.env`** (optional - uses default if not present)

4. **Use in code:**
   ```python
   from config.settings import get_settings
   settings = get_settings()
   value = settings.NEW_CONFIG
   ```

## References

- Pydantic Settings Documentation: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- 12-Factor App Configuration: https://12factor.net/config

"""Centralized configuration settings for all services."""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Service URLs
    USERS_SERVICE_URL: str = "http://users-service:8001"
    SUBMISSION_SERVICE_URL: str = "http://submission-service:8002"
    PLAGIARISM_SERVICE_URL: str = "http://plagiarism-service:8003"
    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8004"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"
    GATEWAY_URL: str = "http://gateway:8000"
    
    # Kafka Configuration
    KAFKA_BROKER: str = "b-1.devmsk.n13jon.c11.kafka.us-east-1.amazonaws.com:9094,b-2.devmsk.n13jon.c11.kafka.us-east-1.amazonaws.com:9094"
    KAFKA_TOPIC_SUBMISSION_UPLOADED: str = "paper_uploaded"
    KAFKA_TOPIC_PLAGIARISM_CHECKED: str = "plagiarism_checked"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Database Configuration - Use environment variables in production
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin123@127.0.0.1:5432/paper_portal"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin123"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "paper_portal"
    
    # MongoDB Configuration
    MONGO_USER: str = "admin"
    MONGO_PASSWORD: str = "admin123"
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "plagiarism_db"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Flink Configuration
    FLINK_MODE: str = "managed"  # Options: "local", "remote", "managed"
    FLINK_JOBMANAGER_HOST: str = "localhost"
    FLINK_JOBMANAGER_PORT: int = 8081
    # For managed Flink (AWS Kinesis, Confluent Cloud, etc.)
    FLINK_MANAGED_ENDPOINT: str = "dev-managed-flink"  # AWS Managed Flink app name
    FLINK_MANAGED_API_KEY: str = ""
    FLINK_MANAGED_API_SECRET: str = ""
    
    # File Upload Configuration
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    @property
    def POSTGRES_URL(self) -> str:
        """Get PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def MONGO_URL(self) -> str:
        """Get MongoDB connection URL."""
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}"
    
    @property
    def REDIS_URL(self) -> str:
        """Get Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from environment
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Centralized configuration settings for all services."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Service URLs
    USERS_SERVICE_URL: str = "http://localhost:8001"
    SUBMISSION_SERVICE_URL: str = "http://localhost:8002"
    PLAGIARISM_SERVICE_URL: str = "http://localhost:8003"
    ANALYTICS_SERVICE_URL: str = "http://localhost:8004"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8005"
    GATEWAY_URL: str = "http://localhost:8000"
    
    # Kafka Configuration
    KAFKA_BROKER: str = "localhost:9092"
    KAFKA_TOPIC_SUBMISSION_UPLOADED: str = "submission_uploaded"
    KAFKA_TOPIC_PLAGIARISM_CHECKED: str = "plagiarism_checked"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Database (if needed in future)
    DATABASE_URL: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

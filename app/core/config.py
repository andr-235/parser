"""Application configuration management."""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with VK API integration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Application Configuration
    APP_NAME: str = Field(default="VK Comments Monitor", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(
        default="development", description="Environment (development/production)"
    )

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # Database Configuration
    DATABASE_URL: str = (
        "postgresql+asyncpg://vk_monitor:dev_password_123@localhost:5432/vk_monitor_dev"
    )
    DATABASE_ECHO: bool = False

    # Redis Configuration
    REDIS_URL: str = "redis://:dev_redis_password@localhost:6379/0"

    # Security Configuration
    SECRET_KEY: str = Field(
        default="vk-monitor-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Token expiration time"
    )

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # VK API Configuration
    VK_ACCESS_TOKEN: str = "your_vk_access_token_here"
    VK_API_VERSION: str = "5.131"
    VK_REQUESTS_PER_SECOND: int = 3
    VK_APP_ID: str = "your_vk_app_id_here"
    VK_MAX_POSTS_PER_REQUEST: int = 100
    VK_MAX_COMMENTS_PER_REQUEST: int = 100
    VK_TIMEOUT_SECONDS: int = 30

    # Background Tasks Configuration
    CELERY_BROKER_URL: str = "redis://:dev_redis_password@localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:dev_redis_password@localhost:6379/2"

    # Monitoring Configuration
    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL_MINUTES: int = 5
    DATA_RETENTION_DAYS: int = 30

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )


# Global settings instance
settings = Settings()

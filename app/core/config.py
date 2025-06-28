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
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vk_monitor:vk_monitor_password"
        "@postgres:5432/vk_monitor_db",
        description="Database connection URL",
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://redis:6379/0", description="Redis connection URL"
    )

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
    VK_API_TOKEN: Optional[str] = Field(default=None, description="VK API access token")
    VK_API_VERSION: str = Field(default="5.131", description="VK API version")
    VK_API_REQUESTS_PER_SECOND: int = Field(
        default=3, description="VK API rate limit (requests per second)"
    )
    VK_API_TIMEOUT: int = Field(
        default=30, description="VK API request timeout in seconds"
    )
    VK_GROUP_ID: Optional[int] = Field(
        default=None, description="Default VK group ID for monitoring"
    )

    # Background Tasks Configuration
    CELERY_BROKER_URL: str = Field(
        default="redis://redis:6379/1", description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://redis:6379/2", description="Celery result backend URL"
    )

    # Monitoring Configuration
    CHECK_INTERVAL_SECONDS: int = Field(
        default=300, description="Default check interval for monitoring tasks (seconds)"
    )
    MAX_COMMENTS_PER_REQUEST: int = Field(
        default=100, description="Maximum comments to fetch per VK API request"
    )
    SENTIMENT_ANALYSIS_ENABLED: bool = Field(
        default=True, description="Enable sentiment analysis for comments"
    )

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )


# Global settings instance
settings = Settings()

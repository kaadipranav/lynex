"""
Configuration module for Ingest API.
Reads environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path

# Find .env file - walk up from current file to find project root
def find_env_file():
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Go up max 5 levels
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        current = current.parent
    return ".env"

ENV_FILE = find_env_file()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the project root (copy from .env.example).
    """

    # ----- Queue Mode -----
    queue_mode: str = Field(
        default="memory",
        description="Queue mode: 'redis', 'upstash', or 'memory' (for local testing)"
    )
    
    # ----- Redis (standard protocol) -----
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL (standard redis:// protocol)"
    )
    
    # ----- Upstash REST API -----
    redis_rest_url: Optional[str] = Field(
        default=None,
        description="Upstash REST API URL"
    )
    redis_rest_token: Optional[str] = Field(
        default=None,
        description="Upstash REST API token"
    )

    # ----- ClickHouse -----
    clickhouse_host: str = Field(
        default="localhost",
        description="ClickHouse server host"
    )
    clickhouse_port: int = Field(
        default=8123,
        description="ClickHouse HTTP port"
    )
    clickhouse_user: str = Field(
        default="default",
        description="ClickHouse username"
    )
    clickhouse_password: str = Field(
        default="",
        description="ClickHouse password"
    )
    clickhouse_database: str = Field(
        default="default",
        description="ClickHouse database name"
    )

    # ----- API Server -----
    api_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the API server"
    )
    api_port: int = Field(
        default=8000,
        description="Port to bind the API server"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    env: str = Field(
        default="development",
        description="Environment: development, staging, or production"
    )

    # ----- Monitoring (Optional) -----
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    # ----- Datadog APM -----
    datadog_enabled: bool = Field(
        default=False,
        description="Enable Datadog APM tracing"
    )
    dd_service: str = Field(
        default="lynex-ingest-api",
        description="Datadog service name"
    )
    dd_env: str = Field(
        default="development",
        description="Datadog environment"
    )
    dd_version: str = Field(
        default="1.0.0",
        description="Application version for Datadog"
    )

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton instance - import this in other modules
settings = Settings()

"""
Configuration module for Ingest API.
Reads environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the project root (copy from .env.example).
    """

    # ----- Redis -----
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL (Upstash recommended)"
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

    # ----- Monitoring (Optional) -----
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance - import this in other modules
settings = Settings()

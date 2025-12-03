"""
Configuration module for Processor Worker.
Reads environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """
    Processor settings loaded from environment variables.
    Uses the same .env file as the ingest-api.
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

    # ----- Worker Settings -----
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    batch_size: int = Field(
        default=10,
        description="Number of events to fetch per batch"
    )
    
    block_timeout_ms: int = Field(
        default=5000,
        description="How long to block waiting for new events (ms)"
    )

    # ----- Monitoring (Optional) -----
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    class Config:
        env_file = "../../.env"  # Relative to processor directory
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()

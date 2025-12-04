"""
Configuration module for Processor Worker.
Reads environment variables using pydantic-settings.
"""

import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).resolve().parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

from shared.config import validate_on_startup


def find_env_file():
    """Find .env file in project root."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        current = current.parent
    return ".env"


ENV_FILE = find_env_file()


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
    env: str = Field(
        default="development",
        description="Environment: development, staging, or production"
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

    # ----- Datadog APM -----
    datadog_enabled: bool = Field(
        default=False,
        description="Enable Datadog APM tracing"
    )
    dd_service: str = Field(
        default="lynex-processor",
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

    # ----- Alerting -----
    alert_webhook_url: Optional[str] = Field(
        default=None,
        description="Webhook URL for alerts"
    )
    slack_webhook_url: Optional[str] = Field(
        default=None,
        description="Slack incoming webhook URL for alerts"
    )

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Singleton instance
settings = Settings()

# Validate on startup
validate_on_startup(
    service_name="Processor",
    required_vars=["REDIS_URL", "CLICKHOUSE_HOST"],
    optional_vars=["SENTRY_DSN", "SLACK_WEBHOOK_URL"],
    env=settings.env
)

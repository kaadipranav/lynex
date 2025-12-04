"""
Configuration module for UI Backend API.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path


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
    """UI Backend API settings."""

    # ----- ClickHouse -----
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=8123)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="default")

    # ----- Redis -----
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)

    # ----- API Server -----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8001)  # Different port from ingest API
    debug: bool = Field(default=True)
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
        default="lynex-ui-backend",
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

    # ----- Auth (Supabase) -----
    supabase_url: str = Field(..., description="Supabase Project URL")
    supabase_anon_key: str = Field(..., description="Supabase Anon Key (Public)")
    supabase_service_key: str = Field(..., description="Supabase Service Role Key (Secret)")
    
    # ----- Admin -----
    admin_api_key: str = Field(..., description="Secret key for admin endpoints")

    # ----- CORS -----
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

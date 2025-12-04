"""
Configuration module for Ingest API.
Reads environment variables using pydantic-settings.
"""

import sys
import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional
from pathlib import Path

# Add shared module to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


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
    Ingest API settings with validation.
    """

    # ----- Environment -----
    env: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Enable debug mode")

    # ----- Queue Mode -----
    queue_mode: str = Field(
        default="redis",
        description="Queue mode: 'redis' or 'memory' (for local testing)"
    )
    
    # ----- Redis -----
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    redis_rest_url: Optional[str] = Field(default=None, description="Upstash REST URL")
    redis_rest_token: Optional[str] = Field(default=None, description="Upstash REST token")

    # ----- ClickHouse -----
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=9000)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="default")

    # ----- API Server -----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8001)

    # ----- Auth (Supabase) -----
    supabase_url: str = Field(default="", description="Supabase Project URL")
    supabase_service_key: str = Field(default="", description="Supabase Service Key")

    # ----- Monitoring -----
    sentry_dsn: Optional[str] = Field(default=None)
    datadog_enabled: bool = Field(default=False)
    dd_service: str = Field(default="lynex-ingest-api")
    dd_env: str = Field(default="development")
    dd_version: str = Field(default="1.0.0")

    @field_validator('env')
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"env must be one of: {allowed}")
        return v

    @field_validator('queue_mode')
    @classmethod
    def validate_queue_mode(cls, v: str) -> str:
        allowed = ['redis', 'memory']
        if v not in allowed:
            raise ValueError(f"queue_mode must be one of: {allowed}")
        return v

    @model_validator(mode='after')
    def validate_production(self) -> 'Settings':
        """Validate production requirements."""
        if self.env == 'production':
            if not self.clickhouse_password:
                import logging
                logging.warning("CLICKHOUSE_PASSWORD not set in production")
        return self

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

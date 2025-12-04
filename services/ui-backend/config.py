"""
Configuration module for UI Backend API.
"""

import sys
import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional, List
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
    """UI Backend API settings with validation."""

    # ----- Environment -----
    env: str = Field(
        default="development",
        description="Environment: development, staging, or production"
    )
    debug: bool = Field(default=True)

    # ----- ClickHouse -----
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=9000)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="default")

    # ----- Redis -----
    redis_url: Optional[str] = Field(default="redis://localhost:6379", description="Redis URL")
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = Field(default=None)

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL, preferring REDIS_URL if set."""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ----- API Server -----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # ----- Monitoring -----
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    datadog_enabled: bool = Field(default=False)
    dd_service: str = Field(default="lynex-ui-backend")
    dd_env: str = Field(default="development")
    dd_version: str = Field(default="1.0.0")

    # ----- Auth (Supabase) -----
    supabase_url: str = Field(default="", description="Supabase Project URL")
    supabase_anon_key: str = Field(default="", description="Supabase Anon Key")
    supabase_service_key: str = Field(default="", description="Supabase Service Role Key")
    
    # ----- Admin -----
    admin_api_key: str = Field(default="dev-admin-key", description="Admin API key")

    # ----- CORS -----
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    @field_validator('env')
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"env must be one of: {allowed}")
        return v

    @model_validator(mode='after')
    def validate_production(self) -> 'Settings':
        """Validate production requirements."""
        if self.env == 'production':
            errors = []
            if not self.supabase_url:
                errors.append("SUPABASE_URL is required")
            if not self.supabase_service_key:
                errors.append("SUPABASE_SERVICE_KEY is required")
            if self.admin_api_key == 'dev-admin-key':
                errors.append("ADMIN_API_KEY must be changed from default")
            if errors:
                import logging
                logging.warning(f"Production validation warnings: {errors}")
        return self

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()

"""
Configuration module for UI Backend API.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """UI Backend API settings."""

    # ----- ClickHouse -----
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=8123)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="default")

    # ----- API Server -----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8001)  # Different port from ingest API
    debug: bool = Field(default=True)

    # ----- Auth (Future) -----
    jwt_secret: str = Field(default="dev-secret-change-in-production")
    
    # ----- CORS -----
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

"""
Billing Configuration.
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
    """Billing service settings."""

    # ----- Redis (for tier storage) -----
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    # ----- Whop -----
    whop_api_key: str = Field(
        default="",
        description="Whop API key from dashboard"
    )
    whop_webhook_secret: str = Field(
        default="",
        description="Whop webhook signing secret"
    )
    
    # Whop Plan IDs (configure with your actual IDs)
    whop_plan_pro_monthly: str = Field(default="plan_pro_monthly")
    whop_plan_pro_yearly: str = Field(default="plan_pro_yearly")
    whop_plan_business_monthly: str = Field(default="plan_business_monthly")
    whop_plan_business_yearly: str = Field(default="plan_business_yearly")

    # ----- Server -----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8002)
    debug: bool = Field(default=True)
    env: str = Field(default="development")

    # ----- Monitoring -----
    sentry_dsn: Optional[str] = Field(default=None)

    # ----- Datadog APM -----
    datadog_enabled: bool = Field(
        default=False,
        description="Enable Datadog APM tracing"
    )
    dd_service: str = Field(
        default="watchllm-billing",
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


# Singleton instance
settings = Settings()

# Validate on startup
validate_on_startup(
    service_name="Billing",
    required_vars=["REDIS_URL"],
    optional_vars=["SENTRY_DSN", "WHOP_API_KEY", "WHOP_WEBHOOK_SECRET"],
    env=settings.env
)

"""
Billing Configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Billing service settings."""

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

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

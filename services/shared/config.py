"""
Shared Configuration Validation Module.
Provides base settings class and validation utilities for all services.
"""

import os
import sys
import logging
from typing import Optional, List, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pathlib import Path

logger = logging.getLogger("watchllm.config")


def find_env_file() -> str:
    """Find .env file in project root."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        current = current.parent
    return ".env"


class BaseServiceSettings(BaseSettings):
    """
    Base settings class with common configuration and validation.
    All services should inherit from this class.
    """
    
    # ----- Environment -----
    env: str = Field(
        default="development",
        description="Environment: development, staging, or production"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # ----- ClickHouse -----
    clickhouse_host: str = Field(
        default="localhost",
        description="ClickHouse server hostname"
    )
    clickhouse_port: int = Field(
        default=9000,
        description="ClickHouse native protocol port"
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
    
    # ----- Redis -----
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # ----- Supabase -----
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL"
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        description="Supabase anonymous key"
    )
    supabase_service_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key"
    )
    
    # ----- Monitoring -----
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    
    # ----- Admin -----
    admin_api_key: Optional[str] = Field(
        default=None,
        description="Admin API key for manual tier upgrades"
    )
    
    @field_validator('env')
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"env must be one of: {allowed}")
        return v
    
    @field_validator('clickhouse_port')
    @classmethod
    def validate_clickhouse_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("clickhouse_port must be between 1 and 65535")
        return v
    
    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError("redis_url must start with redis:// or rediss://")
        return v
    
    @model_validator(mode='after')
    def validate_production_requirements(self) -> 'BaseServiceSettings':
        """Validate that production has all required secrets."""
        if self.env == 'production':
            errors = []
            
            if not self.clickhouse_password:
                errors.append("CLICKHOUSE_PASSWORD is required in production")
            
            if not self.admin_api_key or self.admin_api_key == 'dev-admin-key-change-in-production':
                errors.append("ADMIN_API_KEY must be set to a secure value in production")
            
            if not self.supabase_url:
                errors.append("SUPABASE_URL is required in production")
            
            if not self.supabase_service_key:
                errors.append("SUPABASE_SERVICE_KEY is required in production")
            
            if errors:
                error_msg = "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
                logger.error(error_msg)
                if not os.getenv("SKIP_VALIDATION"):
                    raise ValueError(error_msg)
        
        return self
    
    def log_config_summary(self, service_name: str):
        """Log a summary of the configuration (without secrets)."""
        logger.info(f"{'='*60}")
        logger.info(f"  {service_name} Configuration")
        logger.info(f"{'='*60}")
        logger.info(f"  Environment: {self.env}")
        logger.info(f"  Debug: {self.debug}")
        logger.info(f"  ClickHouse: {self.clickhouse_host}:{self.clickhouse_port}")
        logger.info(f"  Redis: {self.redis_url[:30]}...")
        logger.info(f"  Supabase: {'configured' if self.supabase_url else 'not configured'}")
        logger.info(f"  Sentry: {'configured' if self.sentry_dsn else 'not configured'}")
        logger.info(f"{'='*60}")

    class Config:
        env_file = find_env_file()
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


def validate_startup(settings: BaseServiceSettings, service_name: str) -> bool:
    """
    Validate configuration on service startup.
    Returns True if valid, raises exception if critical errors.
    """
    logger.info(f"Validating configuration for {service_name}...")
    
    warnings = []
    
    # Check optional but recommended settings
    if not settings.sentry_dsn:
        warnings.append("SENTRY_DSN not configured - error tracking disabled")
    
    if settings.env == 'development' and not settings.debug:
        warnings.append("DEBUG is false in development environment")
    
    if settings.env == 'production' and settings.debug:
        warnings.append("DEBUG is true in production environment (not recommended)")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"⚠️  {warning}")
    
    # Log summary
    settings.log_config_summary(service_name)
    
    return True


def validate_on_startup(
    service_name: str,
    required_vars: List[str],
    optional_vars: Optional[List[str]] = None,
    env: str = "development"
) -> bool:
    """
    Validate environment variables on service startup.
    This is a compatibility wrapper for config files that call validate_on_startup.
    
    Args:
        service_name: Name of the service being validated
        required_vars: List of required environment variable names
        optional_vars: List of optional environment variable names (for warnings)
        env: Environment name (development, staging, production)
    
    Returns:
        True if validation passes
    
    Raises:
        ValueError: If required variables are missing in production
    """
    if optional_vars is None:
        optional_vars = []
    
    logger.info(f"Validating environment variables for {service_name}...")
    
    missing_required = []
    missing_optional = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_required.append(var)
        else:
            logger.debug(f"✓ Required: {var}")
    
    # Check optional variables (for warnings only)
    for var in optional_vars:
        value = os.getenv(var)
        if not value:
            missing_optional.append(var)
        else:
            logger.debug(f"✓ Optional: {var}")
    
    # In production, fail if required vars are missing
    if env == "production" and missing_required:
        error_msg = f"Production configuration error for {service_name}:\n"
        error_msg += "\n".join(f"  - Missing required: {var}" for var in missing_required)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Log warnings for missing optional vars
    if missing_optional:
        logger.warning(f"⚠️  Optional variables not set: {', '.join(missing_optional)}")
    
    # Log warnings for missing required vars in non-production
    if missing_required and env != "production":
        logger.warning(f"⚠️  Required variables not set (will use defaults): {', '.join(missing_required)}")
    
    logger.info(f"✓ Configuration validation complete for {service_name}")
    return True
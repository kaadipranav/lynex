import sentry_sdk
import os
import logging
from typing import List, Optional

def init_sentry(
    dsn: str,
    environment: str = "development",
    service_name: str = "unknown-service",
    traces_sample_rate: float = 0.1,
    integrations: Optional[List] = None
):
    """
    Initialize Sentry SDK with common configuration.
    """
    if not dsn:
        logging.warning("Sentry DSN not provided. Skipping initialization.")
        return

    if integrations is None:
        integrations = []
    
    # Add LoggingIntegration by default if not present
    from sentry_sdk.integrations.logging import LoggingIntegration
    has_logging = any(isinstance(i, LoggingIntegration) for i in integrations)
    if not has_logging:
        integrations.append(
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
        )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        integrations=integrations,
    )
    sentry_sdk.set_tag("service", service_name)
    
    # Set user context if available in env (fallback)
    # Real user context should be set in middleware
    if os.getenv("HOSTNAME"):
        sentry_sdk.set_context("system", {"hostname": os.getenv("HOSTNAME")})

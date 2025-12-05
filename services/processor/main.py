"""
Processor Worker - Main Entry Point
Consumes events from Redis Stream and processes them.
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime

# Add shared module to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.sentry_config import init_sentry
from shared.logging_config import configure_logging
from shared.database import db

import sentry_sdk

# Try to import ddtrace (may fail on Python 3.13+)
try:
    from ddtrace import patch_all
    DDTRACE_AVAILABLE = True
except ImportError:
    DDTRACE_AVAILABLE = False
    patch_all = None

from consumer import EventConsumer
from config import settings
import clickhouse
from alerts import rule_manager

# =============================================================================
# Logging Setup
# =============================================================================

configure_logging(
    service_name="processor",
    environment=settings.env,
    log_level="DEBUG" if settings.debug else "INFO"
)
logger = logging.getLogger("watchllm.processor")


# =============================================================================
# Sentry Initialization
# =============================================================================

init_sentry(
    dsn=settings.sentry_dsn,
    environment=settings.env,
    service_name="processor"
)


# =============================================================================
# Graceful Shutdown
# =============================================================================

shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()


async def refresh_rules_loop(shutdown_event: asyncio.Event):
    """Periodically refresh alert rules."""
    while not shutdown_event.is_set():
        await rule_manager.load_rules()
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=60)
        except asyncio.TimeoutError:
            continue


# =============================================================================
# Main Worker Loop
# =============================================================================

async def main():
    """Main worker entry point."""
    logger.info("🚀 WatchLLM - Processor Worker starting...")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   Redis: {settings.redis_url[:30]}...")
    logger.info(f"   ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    # Initialize Sentry
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from shared.sentry_config import init_sentry
    
    init_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        service_name="processor"
    )
    
    # Initialize Datadog APM
    if settings.datadog_enabled and DDTRACE_AVAILABLE:
        os.environ["DD_SERVICE"] = settings.dd_service
    # Connect to MongoDB
    db.connect()
    await db.ping()
    
    # Load initial rules
    await rule_manager.load_rules()
    
    # Start rule refresh task
    refresh_task = asyncio.create_task(refresh_rules_loop(shutdown_event))
    
    # Create consumer
    consumer = EventConsumer()tadog enabled but ddtrace not available (Python 3.13+ compatibility issue)")
    else:
        logger.info("ℹ️  Datadog APM disabled")
    
    # Connect to MongoDB
    db.connect()
    await db.ping()
    
    # Create consumer
    consumer = EventConsumer()
    
    try:
        # Initialize consumer (connect to Redis, create consumer group)
        await consumer.initialize()
        
        # Connect to ClickHouse
        try:
            await clickhouse.get_clickhouse_client()
    finally:
        # Cleanup
        if 'refresh_task' in locals():
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass
        
        db.close()
        await consumer.close()rocessor cannot function without ClickHouse.")
            raise e
        
        # Start consuming events
        logger.info("📥 Starting event consumption loop...")
        await consumer.consume_loop(shutdown_event)
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        db.close()
        await consumer.close()
        await clickhouse.close_clickhouse_client()
        logger.info("👋 Processor Worker shut down complete")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the async main loop
    asyncio.run(main())

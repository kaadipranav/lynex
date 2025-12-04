"""
Processor Worker - Main Entry Point
Consumes events from Redis Stream and processes them.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

import sentry_sdk

import os

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

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("lynex.processor")


# =============================================================================
# Graceful Shutdown
# =============================================================================

shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()


# =============================================================================
# Main Worker Loop
# =============================================================================

async def main():
    """Main worker entry point."""
    logger.info("🚀 Lynex - Processor Worker starting...")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   Redis: {settings.redis_url[:30]}...")
    logger.info(f"   ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    # Initialize Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.env,
            traces_sample_rate=1.0 if settings.debug else 0.1,
            release=f"lynex-processor@1.0.0",
            server_name="processor",
        )
        logger.info("✅ Sentry initialized for error tracking")
    else:
        logger.warning("⚠️  Sentry DSN not configured")
    
    # Initialize Datadog APM
    if settings.datadog_enabled and DDTRACE_AVAILABLE:
        os.environ["DD_SERVICE"] = settings.dd_service
        os.environ["DD_ENV"] = settings.dd_env
        os.environ["DD_VERSION"] = settings.dd_version
        patch_all()
        logger.info(f"✅ Datadog APM initialized (service: {settings.dd_service})")
    elif settings.datadog_enabled and not DDTRACE_AVAILABLE:
        logger.warning("⚠️  Datadog enabled but ddtrace not available (Python 3.13+ compatibility issue)")
    else:
        logger.info("ℹ️  Datadog APM disabled")
    
    # Create consumer
    consumer = EventConsumer()
    
    try:
        # Initialize consumer (connect to Redis, create consumer group)
        await consumer.initialize()
        
        # Connect to ClickHouse
        try:
            await clickhouse.get_clickhouse_client()
            logger.info("   ClickHouse: Connected ✅")
        except Exception as e:
            logger.error(f"   ClickHouse: Connection failed ❌ - {e}")
            logger.error("   Processor cannot function without ClickHouse.")
        
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

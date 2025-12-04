"""
Lynex — Query API (UI Backend)
Provides read-only endpoints for the dashboard.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys

# Add shared module to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.sentry_config import init_sentry
from shared.logging_config import configure_logging
from shared.database import db
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Try to import ddtrace (may fail on Python 3.13+)
try:
    from ddtrace import tracer, patch_all
    DDTRACE_AVAILABLE = True
except ImportError:
    DDTRACE_AVAILABLE = False
    tracer = None
    patch_all = None

from config import settings
from routes.events import router as events_router
from routes.stats import router as stats_router
from routes.projects import router as projects_router
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.subscription import router as subscription_router
import clickhouse as ch
import redis_client

# =============================================================================
# Logging Setup
# =============================================================================

configure_logging(
    service_name="ui-backend",
    environment=settings.env,
    log_level="DEBUG" if settings.debug else "INFO"
)
logger = logging.getLogger("lynex.query")


# =============================================================================
# Sentry Initialization
# =============================================================================

init_sentry(
    dsn=settings.sentry_dsn,
    environment=settings.env,
    service_name="ui-backend",
    integrations=[FastApiIntegration(transaction_style="endpoint")]
)


# =============================================================================
# Datadog APM Initialization
# =============================================================================

if settings.datadog_enabled and DDTRACE_AVAILABLE:
    # Set Datadog environment variables
    os.environ["DD_SERVICE"] = settings.dd_service
    os.environ["DD_ENV"] = settings.dd_env
    os.environ["DD_VERSION"] = settings.dd_version
    os.environ["DD_LOGS_INJECTION"] = "true"
    os.environ["DD_TRACE_SAMPLE_RATE"] = "1.0" if settings.debug else "0.1"
    
    # Auto-instrument FastAPI, HTTP clients
    patch_all()
    
    logger.info(f"✅ Datadog APM initialized (service: {settings.dd_service})")
elif settings.datadog_enabled and not DDTRACE_AVAILABLE:
    logger.warning("⚠️  Datadog enabled but ddtrace not available (Python 3.13+ compatibility issue)")
else:
    logger.info("ℹ️  Datadog APM disabled")


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Lynex - UI Backend starting...")
    logger.info(f"   Server: {settings.api_host}:{settings.api_port}")
    
    # Connect to MongoDB
    db.connect()
    await db.ping()
    
    # Connect to ClickHouse
    try:
        await ch.get_client()
        logger.info("   ClickHouse: Connected ✅")
    except Exception as e:
        logger.error(f"   ClickHouse: Connection failed ❌ - {e}")
        if settings.env == "production":
            raise e

    # Connect to Redis
    try:
        await redis_client.get_redis_client()
        logger.info("   Redis: Connected ✅")
    except Exception as e:
        logger.error(f"   Redis: Connection failed ❌ - {e}")
        if settings.env == "production":
            raise e
    
    yield
    
    logger.info("🛑 Shutting down...")
    db.close()
    if ch._client:
        await ch._client.close()
    await redis_client.close_redis_client()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Lynex - Query API",
    description="Read-only API for dashboard queries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
)


# =============================================================================
# CORS Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Routes
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "Lynex - Query API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    try:
        client = await ch.get_client()
        await client.query("SELECT 1")
        return {"status": "healthy"}
    except:
        return {"status": "degraded", "clickhouse": "unavailable"}

app.include_router(events_router, prefix="/api/v1", tags=["Events"])
app.include_router(stats_router, prefix="/api/v1", tags=["Statistics"])
app.include_router(projects_router, prefix="/api/v1", tags=["Projects"])
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(subscription_router, prefix="/api/v1", tags=["Subscription"])
app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])


# =============================================================================
# Run with Uvicorn
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

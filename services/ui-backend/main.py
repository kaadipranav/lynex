"""
Lynex — Query API (UI Backend)
Provides read-only endpoints for the dashboard.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

import os

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
import clickhouse as ch

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("lynex.query")


# =============================================================================
# Sentry Initialization
# =============================================================================

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=1.0 if settings.debug else 0.1,
        profiles_sample_rate=1.0 if settings.debug else 0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        release=f"lynex-ui-backend@1.0.0",
        server_name="ui-backend",
    )
    logger.info("✅ Sentry initialized for error tracking")
else:
    logger.warning("⚠️  Sentry DSN not configured - error tracking disabled")


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
    logger.info("🚀 Lynex - Query API starting...")
    logger.info(f"   Server: {settings.api_host}:{settings.api_port}")
    
    # Connect to ClickHouse (will fallback to mock data if unavailable)
    await ch.get_client()
    if ch.is_using_mock():
        logger.info("   ClickHouse: Using mock data 📦")
    else:
        logger.info("   ClickHouse: Connected ✅")
    
    yield
    
    logger.info("👋 Query API shutting down...")
    await ch.close_client()


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

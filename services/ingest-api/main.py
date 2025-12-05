"""
WatchLLM — Ingest API
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import sys

# Add shared module to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sentry_sdk.integrations.fastapi import FastApiIntegration
from shared.sentry_config import init_sentry
from shared.logging_config import configure_logging
from shared.database import db

# Try to import ddtrace (may fail on Python 3.13+)
try:
    from ddtrace import tracer, patch_all
    DDTRACE_AVAILABLE = True
except ImportError:
    DDTRACE_AVAILABLE = False
    tracer = None
    patch_all = None

from config import settings
from schemas import HealthResponse
from routes.events import router as events_router
import redis_queue as event_queue
import metrics as prom_metrics


# =============================================================================
# Logging Setup
# =============================================================================

configure_logging(
    service_name="ingest-api",
    environment=settings.env,
    log_level="DEBUG" if settings.debug else "INFO"
)
logger = logging.getLogger("watchllm.ingest")


# =============================================================================
# Sentry Initialization
# =============================================================================

init_sentry(
    dsn=settings.sentry_dsn,
    environment=settings.env,
    service_name="ingest-api",
    integrations=[FastApiIntegration(transaction_style="endpoint")]
)


init_sentry(
    dsn=settings.sentry_dsn,
    environment=settings.env,
    service_name="ingest-api",
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
    
    # Auto-instrument FastAPI, Redis, HTTP clients
    patch_all()
    
    logger.info(f"✅ Datadog APM initialized (service: {settings.dd_service})")
elif settings.datadog_enabled and not DDTRACE_AVAILABLE:
    logger.warning("⚠️  Datadog enabled but ddtrace not available (Python 3.13+ compatibility issue)")
else:
    logger.info("ℹ️  Datadog APM disabled")


# =============================================================================
# Lifespan (Startup/Shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 WatchLLM - Ingest API starting...")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   Server: {settings.api_host}:{settings.api_port}")
    
    # Connect to MongoDB (optional for demo mode)
    try:
        db.connect()
        await db.ping()
        logger.info("✅ MongoDB connected")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB not available (demo mode): {e}")
    
    # Connect to Redis (optional for demo mode)
    try:
        await event_queue.get_redis_client()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available (demo mode): {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    try:
        db.close()
        await event_queue.close_redis_client()
    except:
        pass


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="WatchLLM - Ingest API",
    description="AI Observability Platform - Event Ingestion Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# =============================================================================
# Middleware
# =============================================================================

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None,
            "status_code": 500
        }
    )


# =============================================================================
# Routes
# =============================================================================

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint with Redis status."""
    redis_healthy = await event_queue.health_check()
    status = "healthy" if redis_healthy else "degraded"
    return HealthResponse(status=status)


# Prometheus metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint for monitoring."""
    from fastapi.responses import Response
    return Response(
        content=prom_metrics.get_metrics(),
        media_type=prom_metrics.get_content_type(),
    )


# Queue stats endpoint
@app.get("/health/queue", tags=["Health"])
async def queue_health():
    """Get queue statistics."""
    try:
        stats = await event_queue.get_queue_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "service": "WatchLLM - Ingest API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Disabled in production"
    }


# Sentry test endpoint (only in debug mode)
if settings.debug:
    @app.get("/sentry-test", tags=["Health"])
    async def sentry_test():
        """Test Sentry error tracking - only available in debug mode"""
        logger.info("Triggering test error for Sentry")
        raise Exception("🧪 This is a test error for Sentry! If you see this in Sentry dashboard, integration is working.")


# Event ingestion routes
app.include_router(events_router, prefix="/api/v1", tags=["Events"])


# =============================================================================
# Run with Uvicorn (for development)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )

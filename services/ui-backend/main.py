"""
Sentry for AI — Query API (UI Backend)
Provides read-only endpoints for the dashboard.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from routes.events import router as events_router
from routes.stats import router as stats_router
import clickhouse as ch

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("sentryai.query")


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Sentry for AI - Query API starting...")
    logger.info(f"   Server: {settings.api_host}:{settings.api_port}")
    
    try:
        await ch.get_client()
        logger.info("   ClickHouse: Connected ✅")
    except Exception as e:
        logger.warning(f"   ClickHouse: Not available - {e}")
    
    yield
    
    logger.info("👋 Query API shutting down...")
    await ch.close_client()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Sentry for AI - Query API",
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
        "service": "Sentry for AI - Query API",
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

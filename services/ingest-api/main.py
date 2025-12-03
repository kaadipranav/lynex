"""
Sentry for AI — Ingest API
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from schemas import HealthResponse
from routes.events import router as events_router


# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("sentryai.ingest")


# =============================================================================
# Lifespan (Startup/Shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("🚀 Sentry for AI - Ingest API starting...")
    logger.info(f"   Debug mode: {settings.debug}")
    logger.info(f"   Server: {settings.api_host}:{settings.api_port}")
    
    yield
    
    # Shutdown
    logger.info("👋 Sentry for AI - Ingest API shutting down...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Sentry for AI - Ingest API",
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
    """Health check endpoint."""
    return HealthResponse(status="healthy")


# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "service": "Sentry for AI - Ingest API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Disabled in production"
    }


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

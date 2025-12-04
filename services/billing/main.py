"""
Lynex — Billing Service
Handles subscriptions, usage tracking, and Whop integration.
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

from config import settings
from routes import router as billing_router

# =============================================================================
# Logging Setup
# =============================================================================

configure_logging(
    service_name="billing",
    environment=settings.env,
    log_level="DEBUG" if settings.debug else "INFO"
)
logger = logging.getLogger("lynex.billing")


# =============================================================================
# Sentry Initialization
# =============================================================================

from sentry_sdk.integrations.fastapi import FastApiIntegration

init_sentry(
    dsn=settings.sentry_dsn,
    environment=settings.env,
    service_name="billing",
    integrations=[FastApiIntegration(transaction_style="endpoint")]
)


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Lynex - Billing Service starting...")
    
    # Connect to MongoDB
    db.connect()
    await db.ping()
    
    yield
    
    logger.info("🛑 Shutting down...")
    db.close()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Lynex - Billing Service",
    description="Subscription and usage management with Whop",
    version="1.0.0",
    lifespan=lifespan,

    docs_url="/docs" if settings.debug else None,
)


# =============================================================================
# CORS Middleware
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
        "service": "Lynex - Billing Service",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(billing_router, prefix="/api/v1", tags=["Billing"])


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

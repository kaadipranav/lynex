"""
Sentry for AI — Billing Service
Handles subscriptions, usage tracking, and Whop integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings
from routes import router as billing_router

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("sentryai.billing")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Sentry for AI - Billing Service",
    description="Subscription and usage management with Whop",
    version="1.0.0",
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
        "service": "Sentry for AI - Billing Service",
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

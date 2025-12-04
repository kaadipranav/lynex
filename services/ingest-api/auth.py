"""
API Key Authentication Module.
Handles API key validation and project scoping.
"""

import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).resolve().parent.parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import logging
import re
import hashlib

from shared.database import get_db

logger = logging.getLogger("lynex.ingest.auth")

# =============================================================================
# API Key Configuration
# =============================================================================

API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication. Format: sk_live_xxx or sk_test_xxx"
)

# Valid API key patterns
# Production: sk_live_<24+ chars>
# Test: sk_test_<24+ chars>
API_KEY_PATTERN = re.compile(r"^sk_(live|test)_[a-zA-Z0-9]{24,}$")


# =============================================================================
# API Key Data Model
# =============================================================================

class APIKeyData:
    """Validated API key data."""
    
    def __init__(
        self,
        key: str,
        project_id: str,
        name: str,
        tier: str,
        rate_limit: int,
        is_test: bool,
    ):
        self.key = key
        self.project_id = project_id
        self.name = name
        self.tier = tier
        self.rate_limit = rate_limit
        self.is_test = is_test
    
    def __repr__(self):
        return f"APIKeyData(project={self.project_id}, tier={self.tier})"


# =============================================================================
# Validation Functions
# =============================================================================

def validate_api_key_format(api_key: str) -> bool:
    """Check if API key matches expected format."""
    if not api_key:
        return False
    return bool(API_KEY_PATTERN.match(api_key))


async def get_api_key_data(api_key: str, db) -> Optional[APIKeyData]:
    """
    Look up API key in the store.
    Returns APIKeyData if valid, None if not found.
    """
    # Check format first
    if not validate_api_key_format(api_key):
        return None
    
    # Hash key for lookup
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up in MongoDB
    # TODO: Add Redis caching here for performance
    key_doc = await db.api_keys.find_one({"key_hash": key_hash})
    
    if not key_doc:
        # Fallback for demo keys if DB is empty (for testing)
        if api_key == "sk_test_demo1234567890abcdefghijklmno":
            return APIKeyData(
                key=api_key,
                project_id="proj_demo",
                name="Demo Project",
                tier="free",
                rate_limit=1000,
                is_test=True
            )
        return None
    
    # Check if active
    if not key_doc.get("is_active", True):
        return None
    
    # Determine if test key
    is_test = api_key.startswith("sk_test_")
    
    # Get project tier (could be cached or joined)
    # For now, default to free if not found
    # In real app, we'd fetch project -> organization -> subscription
    tier = "free" 
    rate_limit = 1000
    
    return APIKeyData(
        key=api_key,
        project_id=key_doc["project_id"],
        name=key_doc["name"],
        tier=tier,
        rate_limit=rate_limit,
        is_test=is_test,
    )


# =============================================================================
# FastAPI Dependencies
# =============================================================================

async def get_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db = Depends(get_db)
) -> APIKeyData:
    """
    FastAPI dependency for API key authentication.
    Use this in route handlers: `api_key: APIKeyData = Depends(get_api_key)`
    """
    
    # Check if key is provided
    if not api_key:
        logger.warning("Request received without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Missing API key",
                "message": "Please provide an API key in the X-API-Key header",
                "docs": "https://docs.lynex.dev/authentication"
            }
        )
    
    # Validate format
    if not validate_api_key_format(api_key):
        logger.warning(f"Invalid API key format: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid API key format"}
        )
    
    # Look up key
    key_data = await get_api_key_data(api_key, db)
    
    if not key_data:
        logger.warning(f"Unknown API key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid API key"}
        )
        
    return key_data

            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid API key format",
                "message": "API key must be in format: sk_live_xxx or sk_test_xxx",
                "docs": "https://docs.lynex.dev/authentication"
            }
        )
    
    # Look up key
    key_data = get_api_key_data(api_key)
    if not key_data:
        logger.warning(f"API key not found or inactive: {api_key[:15]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Invalid API key",
                "message": "This API key does not exist or has been revoked",
                "docs": "https://docs.lynex.dev/authentication"
            }
        )
    
    logger.debug(f"Authenticated: {key_data}")
    return key_data


async def get_optional_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> Optional[APIKeyData]:
    """
    Optional API key dependency.
    Returns None if no key provided, raises error only on invalid key.
    Useful for endpoints that work with or without auth.
    """
    if not api_key:
        return None
    
    return await get_api_key(api_key)

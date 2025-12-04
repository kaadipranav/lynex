"""
API Key Authentication Module.
Handles API key validation and project scoping.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional
import logging
import re

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
# Mock API Key Store (Replace with DB in Task 5+)
# =============================================================================

# For MVP, we use a hardcoded dictionary
# In production, this would query Redis/Postgres
MOCK_API_KEYS = {
    "sk_test_demo1234567890abcdefghijklmno": {
        "project_id": "proj_demo",
        "name": "Demo Project",
        "tier": "free",
        "rate_limit": 1000,  # requests per minute
        "active": True,
    },
    "sk_live_prod1234567890abcdefghijklmno": {
        "project_id": "proj_production",
        "name": "Production Project", 
        "tier": "pro",
        "rate_limit": 10000,
        "active": True,
    },
}


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


def get_api_key_data(api_key: str) -> Optional[APIKeyData]:
    """
    Look up API key in the store.
    Returns APIKeyData if valid, None if not found.
    """
    # Check format first
    if not validate_api_key_format(api_key):
        return None
    
    # Look up in mock store (replace with DB query later)
    key_info = MOCK_API_KEYS.get(api_key)
    if not key_info:
        return None
    
    # Check if active
    if not key_info.get("active", False):
        return None
    
    # Determine if test key
    is_test = api_key.startswith("sk_test_")
    
    return APIKeyData(
        key=api_key,
        project_id=key_info["project_id"],
        name=key_info["name"],
        tier=key_info["tier"],
        rate_limit=key_info["rate_limit"],
        is_test=is_test,
    )


# =============================================================================
# FastAPI Dependencies
# =============================================================================

async def get_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
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

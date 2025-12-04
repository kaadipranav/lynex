"""
Supabase Authentication Middleware.
Validates JWT tokens from Supabase Auth.
"""

import os
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from pydantic import BaseModel

from config import settings

# Initialize Supabase client
# We use the service role key for admin tasks if needed, but for middleware
# we primarily verify the JWT.
# Note: In a real production setup, you might verify JWTs locally using the JWT secret
# to avoid a network round-trip on every request, or use the Supabase client's getUser.

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)

security = HTTPBearer(auto_error=False)

class User(BaseModel):
    id: str
    email: str
    role: str = "authenticated"
    app_metadata: Dict[str, Any] = {}
    user_metadata: Dict[str, Any] = {}
    aud: str = "authenticated"
    created_at: str

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Validate the JWT token with Supabase and return the user.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        # This makes a network request. For high performance, verify JWT signature locally.
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            return None
            
        user_data = user_response.user
        
        return User(
            id=user_data.id,
            email=user_data.email,
            role=user_data.role,
            app_metadata=user_data.app_metadata,
            user_metadata=user_data.user_metadata,
            aud=user_data.aud,
            created_at=user_data.created_at
        )
        
    except Exception as e:
        # logger.error(f"Auth error: {e}")
        return None

async def require_user(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authentication. Raise 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

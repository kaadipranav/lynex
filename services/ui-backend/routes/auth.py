"""
Authentication Routes.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from auth import (
    LoginRequest, SignupRequest, AuthResponse, User,
    login, signup, get_current_user, logout
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    return await get_current_user(credentials.credentials)


async def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    """Require authentication, raise 401 if not authenticated."""
    user = await get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/auth/signup", response_model=AuthResponse)
async def signup_route(data: SignupRequest):
    """Create a new user account."""
    try:
        return await signup(data.email, data.password, data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=AuthResponse)
async def login_route(data: LoginRequest):
    """Authenticate and get session token."""
    try:
        return await login(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/logout")
async def logout_route(user: User = Depends(require_user)):
    """Logout current session."""
    return {"success": True}


@router.get("/auth/me", response_model=User)
async def get_me(user: User = Depends(require_user)):
    """Get current authenticated user."""
    return user

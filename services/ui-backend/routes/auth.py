"""
Authentication Routes.
Delegates authentication to Supabase, but provides user context endpoints.
"""

from fastapi import APIRouter, Depends
from auth.supabase_middleware import require_user, User

router = APIRouter()

@router.get("/auth/me", response_model=User)
async def get_me(user: User = Depends(require_user)):
    """Get current authenticated user from Supabase token."""
    return user


"""
User and API Key Models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserProfile(BaseModel):
    id: str  # Supabase User ID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class APIKey(BaseModel):
    id: str
    user_id: str
    name: str
    key_prefix: str
    key_hash: str  # Stored hashed
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str  # Only returned once on creation
    created_at: datetime

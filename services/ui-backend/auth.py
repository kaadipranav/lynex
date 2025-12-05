"""
Authentication module using Appwrite.
For MVP, includes a local fallback if Appwrite is not configured.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import hashlib
import secrets
import jwt

from config import settings

logger = logging.getLogger("watchllm.auth")


# =============================================================================
# Models
# =============================================================================

class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime


class Session(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    user: User
    token: str
    expires_at: datetime


# =============================================================================
# In-Memory User Store (MVP fallback when Appwrite not configured)
# =============================================================================

USERS: dict[str, dict] = {
    "user_demo": {
        "id": "user_demo",
        "email": "demo@watchllm.dev",
        "name": "Demo User",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "created_at": datetime(2024, 1, 1),
    }
}

SESSIONS: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def generate_token(user_id: str) -> tuple[str, datetime]:
    """Generate a JWT token."""
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    payload = {
        "user_id": user_id,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_at


def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id if valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


# =============================================================================
# Auth Functions (Local Implementation)
# =============================================================================

async def signup(email: str, password: str, name: Optional[str] = None) -> AuthResponse:
    """Create a new user account."""
    
    # Check if email already exists
    for user in USERS.values():
        if user["email"] == email:
            raise ValueError("Email already registered")
    
    # Create user
    user_id = f"user_{secrets.token_hex(8)}"
    now = datetime.utcnow()
    
    USERS[user_id] = {
        "id": user_id,
        "email": email,
        "name": name,
        "password_hash": hash_password(password),
        "created_at": now,
    }
    
    # Generate session
    token, expires_at = generate_token(user_id)
    
    return AuthResponse(
        user=User(id=user_id, email=email, name=name, created_at=now),
        token=token,
        expires_at=expires_at,
    )


async def login(email: str, password: str) -> AuthResponse:
    """Authenticate user and return session."""
    
    # Find user by email
    user_data = None
    for user in USERS.values():
        if user["email"] == email:
            user_data = user
            break
    
    if not user_data:
        raise ValueError("Invalid email or password")
    
    if not verify_password(password, user_data["password_hash"]):
        raise ValueError("Invalid email or password")
    
    # Generate session
    token, expires_at = generate_token(user_data["id"])
    
    return AuthResponse(
        user=User(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            created_at=user_data["created_at"],
        ),
        token=token,
        expires_at=expires_at,
    )


async def get_current_user(token: str) -> Optional[User]:
    """Get user from token."""
    user_id = verify_token(token)
    if not user_id:
        return None
    
    user_data = USERS.get(user_id)
    if not user_data:
        return None
    
    return User(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        created_at=user_data["created_at"],
    )


async def logout(token: str) -> bool:
    """Invalidate a session (for JWT, this is a no-op on server side)."""
    # With JWT, we can't truly invalidate without a blacklist
    # For MVP, we just return True
    return True

"""
Project and API Key Management Routes.
CRUD operations for projects and their API keys.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import secrets
import hashlib

router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable name for the key")
    environment: str = Field(default="test", pattern="^(test|live)$")


class APIKey(BaseModel):
    id: str
    project_id: str
    name: str
    environment: str
    key_prefix: str  # First 8 chars for identification
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool = True


class APIKeyWithSecret(APIKey):
    """Returned only on creation - includes full key."""
    key: str


# =============================================================================
# In-Memory Store (Replace with DB later)
# =============================================================================

# Projects store
PROJECTS: dict[str, dict] = {
    "proj_demo": {
        "id": "proj_demo",
        "name": "Demo Project",
        "description": "Default demo project for testing",
        "created_at": datetime(2024, 1, 1),
        "updated_at": datetime(2024, 1, 1),
    }
}

# API Keys store - key_hash -> key_data
API_KEYS: dict[str, dict] = {}

# Key lookup - key_prefix -> key_hash (for finding keys by prefix)
KEY_PREFIX_INDEX: dict[str, str] = {}

# Initialize demo keys
def _init_demo_keys():
    demo_keys = [
        ("sk_test_demo1234567890abcdefghijklmno", "Demo Test Key", "test"),
        ("sk_live_prod1234567890abcdefghijklmno", "Demo Live Key", "live"),
    ]
    for key, name, env in demo_keys:
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        API_KEYS[key_hash] = {
            "id": key_id,
            "project_id": "proj_demo",
            "name": name,
            "environment": env,
            "key_prefix": key[:12],
            "key_hash": key_hash,
            "created_at": datetime(2024, 1, 1),
            "last_used_at": None,
            "is_active": True,
        }
        KEY_PREFIX_INDEX[key[:12]] = key_hash

_init_demo_keys()


# =============================================================================
# Helper Functions
# =============================================================================

def generate_api_key(environment: str) -> str:
    """Generate a new API key."""
    prefix = f"sk_{environment}_"
    random_part = secrets.token_hex(16)  # 32 chars
    return prefix + random_part


def hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


# =============================================================================
# Project Endpoints
# =============================================================================

@router.get("/projects", response_model=List[Project])
async def list_projects():
    """List all projects."""
    return [Project(**p) for p in PROJECTS.values()]


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate):
    """Create a new project."""
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    
    project = {
        "id": project_id,
        "name": data.name,
        "description": data.description,
        "created_at": now,
        "updated_at": now,
    }
    
    PROJECTS[project_id] = project
    return Project(**project)


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a project by ID."""
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**PROJECTS[project_id])


@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, data: ProjectUpdate):
    """Update a project."""
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = PROJECTS[project_id]
    
    if data.name is not None:
        project["name"] = data.name
    if data.description is not None:
        project["description"] = data.description
    
    project["updated_at"] = datetime.utcnow()
    
    return Project(**project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Delete a project and all its API keys."""
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete associated API keys
    keys_to_delete = [
        key_hash for key_hash, key_data in API_KEYS.items()
        if key_data["project_id"] == project_id
    ]
    for key_hash in keys_to_delete:
        key_data = API_KEYS.pop(key_hash)
        KEY_PREFIX_INDEX.pop(key_data["key_prefix"], None)
    
    del PROJECTS[project_id]


# =============================================================================
# API Key Endpoints
# =============================================================================

@router.get("/projects/{project_id}/keys", response_model=List[APIKey])
async def list_api_keys(project_id: str):
    """List all API keys for a project."""
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    keys = [
        APIKey(**{k: v for k, v in key_data.items() if k != "key_hash"})
        for key_data in API_KEYS.values()
        if key_data["project_id"] == project_id
    ]
    return keys


@router.post("/projects/{project_id}/keys", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(project_id: str, data: APIKeyCreate):
    """
    Create a new API key.
    
    ⚠️ The full key is only returned once. Store it securely!
    """
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate key
    raw_key = generate_api_key(data.environment)
    key_hash = hash_key(raw_key)
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    
    key_data = {
        "id": key_id,
        "project_id": project_id,
        "name": data.name,
        "environment": data.environment,
        "key_prefix": raw_key[:12],
        "key_hash": key_hash,
        "created_at": datetime.utcnow(),
        "last_used_at": None,
        "is_active": True,
    }
    
    API_KEYS[key_hash] = key_data
    KEY_PREFIX_INDEX[raw_key[:12]] = key_hash
    
    return APIKeyWithSecret(
        **{k: v for k, v in key_data.items() if k != "key_hash"},
        key=raw_key
    )


@router.delete("/projects/{project_id}/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(project_id: str, key_id: str):
    """Revoke (delete) an API key."""
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find the key
    key_hash_to_delete = None
    for key_hash, key_data in API_KEYS.items():
        if key_data["id"] == key_id and key_data["project_id"] == project_id:
            key_hash_to_delete = key_hash
            break
    
    if not key_hash_to_delete:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key_data = API_KEYS.pop(key_hash_to_delete)
    KEY_PREFIX_INDEX.pop(key_data["key_prefix"], None)


@router.post("/projects/{project_id}/keys/{key_id}/regenerate", response_model=APIKeyWithSecret)
async def regenerate_api_key(project_id: str, key_id: str):
    """
    Regenerate an API key (creates new key, invalidates old one).
    
    ⚠️ The full key is only returned once. Store it securely!
    """
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find existing key
    old_key_hash = None
    old_key_data = None
    for key_hash, key_data in API_KEYS.items():
        if key_data["id"] == key_id and key_data["project_id"] == project_id:
            old_key_hash = key_hash
            old_key_data = key_data
            break
    
    if not old_key_hash:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Generate new key
    raw_key = generate_api_key(old_key_data["environment"])
    new_key_hash = hash_key(raw_key)
    
    # Update key data
    new_key_data = {
        **old_key_data,
        "key_prefix": raw_key[:12],
        "key_hash": new_key_hash,
        "created_at": datetime.utcnow(),  # Reset creation time
    }
    
    # Remove old, add new
    API_KEYS.pop(old_key_hash)
    KEY_PREFIX_INDEX.pop(old_key_data["key_prefix"], None)
    
    API_KEYS[new_key_hash] = new_key_data
    KEY_PREFIX_INDEX[raw_key[:12]] = new_key_hash
    
    return APIKeyWithSecret(
        **{k: v for k, v in new_key_data.items() if k != "key_hash"},
        key=raw_key
    )


# =============================================================================
# Validation Helper (for auth.py)
# =============================================================================

def validate_api_key(raw_key: str) -> Optional[dict]:
    """
    Validate an API key and return its data if valid.
    Used by auth.py for request authentication.
    """
    key_hash = hash_key(raw_key)
    
    if key_hash not in API_KEYS:
        return None
    
    key_data = API_KEYS[key_hash]
    
    if not key_data["is_active"]:
        return None
    
    # Update last_used_at
    key_data["last_used_at"] = datetime.utcnow()
    
    return {
        "key_id": key_data["id"],
        "project_id": key_data["project_id"],
        "environment": key_data["environment"],
    }

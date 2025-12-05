"""
Project model with RBAC support.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProjectRole(str, Enum):
    """Project member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectMember(BaseModel):
    """Project team member."""
    user_id: str
    email: str
    role: ProjectRole
    added_at: datetime
    added_by: str  # user_id who added this member


class Project(BaseModel):
    """Project with team members."""
    project_id: str
    name: str
    description: Optional[str] = None
    owner_id: str  # Creator of the project
    members: List[ProjectMember] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Settings
    settings: dict = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    settings: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Project response schema."""
    project_id: str
    name: str
    description: Optional[str]
    owner_id: str
    role: ProjectRole  # Current user's role
    member_count: int
    created_at: datetime
    updated_at: Optional[datetime]


class AddMemberRequest(BaseModel):
    """Request to add a member to a project."""
    email: str
    role: ProjectRole = ProjectRole.MEMBER


class UpdateMemberRequest(BaseModel):
    """Request to update a member's role."""
    role: ProjectRole

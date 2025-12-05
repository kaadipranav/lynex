"""
Prompt Version Management.
Store and track prompt template versions for diffing and comparison.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PromptVersion(BaseModel):
    """A version of a prompt template."""
    version_id: str
    project_id: str
    prompt_name: str
    version_number: int
    template: str  # The actual prompt template
    variables: Dict[str, Any] = Field(default_factory=dict)  # Template variables
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Model configuration
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # Tracking
    created_by: str  # user_id
    created_at: datetime
    
    # Performance metrics (filled by events)
    usage_count: int = 0
    avg_cost: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    success_rate: Optional[float] = None


class PromptDiff(BaseModel):
    """Difference between two prompt versions."""
    version_a_id: str
    version_b_id: str
    version_a_number: int
    version_b_number: int
    
    # Text differences
    added_lines: List[str] = Field(default_factory=list)
    removed_lines: List[str] = Field(default_factory=list)
    unchanged_lines: List[str] = Field(default_factory=list)
    
    # Metadata changes
    model_changed: bool = False
    temperature_changed: bool = False
    variables_changed: List[str] = Field(default_factory=list)
    
    # Performance comparison
    cost_delta: Optional[float] = None
    latency_delta: Optional[float] = None
    success_rate_delta: Optional[float] = None


class PromptVersionCreate(BaseModel):
    """Schema for creating a new prompt version."""
    prompt_name: str = Field(..., min_length=1, max_length=100)
    template: str = Field(..., min_length=1)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class PromptVersionResponse(BaseModel):
    """Response schema for prompt version."""
    version_id: str
    project_id: str
    prompt_name: str
    version_number: int
    template: str
    variables: Dict[str, Any]
    model: Optional[str]
    created_by: str
    created_at: datetime
    usage_count: int
    avg_cost: Optional[float]
    avg_latency_ms: Optional[float]
    success_rate: Optional[float]

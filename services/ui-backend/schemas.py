"""
Pydantic schemas for Query API responses.
"""

from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel, Field


# =============================================================================
# Event Models
# =============================================================================

class EventResponse(BaseModel):
    """Single event response."""
    event_id: str
    project_id: str
    type: str
    timestamp: datetime
    sdk_name: str
    sdk_version: str
    body: dict[str, Any]
    context: dict[str, Any] = {}
    estimated_cost_usd: float = 0
    queue_latency_ms: float = 0


class EventListResponse(BaseModel):
    """Paginated list of events."""
    events: List[EventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# Stats Models
# =============================================================================

class OverviewStats(BaseModel):
    """Dashboard overview statistics."""
    total_events: int
    total_errors: int
    error_rate_pct: float
    total_cost_usd: float
    total_tokens: int
    avg_latency_ms: Optional[float] = None


class TokenUsageByModel(BaseModel):
    """Token usage grouped by model."""
    model: str
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    request_count: int


class EventCountByType(BaseModel):
    """Event counts grouped by type."""
    type: str
    count: int


class TimeSeriesPoint(BaseModel):
    """Single data point in a time series."""
    timestamp: datetime
    value: float


class TimeSeriesResponse(BaseModel):
    """Time series data."""
    metric: str
    data: List[TimeSeriesPoint]


# =============================================================================
# Error Responses
# =============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None

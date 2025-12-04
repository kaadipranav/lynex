"""
Pydantic schemas for event ingestion.
Based on docs/EVENT_SCHEMA.md
"""

from datetime import datetime
from typing import Optional, Any, Literal, Union
from pydantic import BaseModel, Field
from uuid import uuid4


# =============================================================================
# SDK Info
# =============================================================================

class SDKInfo(BaseModel):
    """SDK identification."""
    name: str = Field(..., description="SDK name (e.g., 'lynex-python')")
    version: str = Field(..., description="SDK version (e.g., '1.0.0')")


# =============================================================================
# Event Body Types
# =============================================================================

class LogEventBody(BaseModel):
    """Log event body."""
    level: Literal["debug", "info", "warn", "error"] = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    metadata: Optional[dict[str, Any]] = None


class ErrorEventBody(BaseModel):
    """Error event body."""
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Stack trace")
    fingerprint: Optional[list[str]] = Field(None, description="Error fingerprint for grouping")
    metadata: Optional[dict[str, Any]] = None


class SpanEventBody(BaseModel):
    """Span event for tracing."""
    span_id: str = Field(..., alias="spanId", description="Unique span identifier")
    parent_span_id: Optional[str] = Field(None, alias="parentSpanId", description="Parent span ID")
    name: str = Field(..., description="Span name")
    start: datetime = Field(..., description="Span start time")
    end: Optional[datetime] = Field(None, description="Span end time")
    attributes: Optional[dict[str, Any]] = None


class TokenUsageEventBody(BaseModel):
    """Token usage event body."""
    model: str = Field(..., description="Model name (e.g., 'gpt-4')")
    input_tokens: int = Field(..., alias="inputTokens", ge=0)
    output_tokens: int = Field(..., alias="outputTokens", ge=0)
    cost_usd: Optional[float] = Field(None, alias="costUSD", ge=0)


class MessageEventBody(BaseModel):
    """Message event body (prompts & responses)."""
    role: Literal["user", "system", "assistant", "tool"]
    content: str
    metadata: Optional[dict[str, Any]] = None


class ModelResponseEventBody(BaseModel):
    """Model response event body."""
    model: str = Field(..., description="Model name")
    prompt: str = Field(..., description="Input prompt")
    response: str = Field(..., description="Model response")
    finish_reason: Optional[str] = Field(None, alias="finishReason")
    latency_ms: int = Field(..., alias="latencyMs", ge=0)
    metadata: Optional[dict[str, Any]] = None


class AgentActionEventBody(BaseModel):
    """Agent action event body."""
    agent_name: Optional[str] = Field(None, alias="agentName")
    action: str = Field(..., description="Action taken")
    input: str = Field(..., description="Action input")
    output: Optional[str] = Field(None, description="Action output")
    reasoning: Optional[str] = Field(None, description="Agent reasoning")
    metadata: Optional[dict[str, Any]] = None


class RetrievalResultItem(BaseModel):
    """Single retrieval result."""
    id: str
    score: float
    text: str
    metadata: Optional[dict[str, Any]] = None


class RetrievalEventBody(BaseModel):
    """Retrieval event body (RAG)."""
    query: str = Field(..., description="Search query")
    results: list[RetrievalResultItem] = Field(default_factory=list)
    vector_dimensions: Optional[int] = Field(None, alias="vectorDimensions")


class ToolCallEventBody(BaseModel):
    """Tool call event body."""
    tool_name: str = Field(..., alias="toolName")
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    latency_ms: Optional[int] = Field(None, alias="latencyMs", ge=0)
    metadata: Optional[dict[str, Any]] = None


class EvalMetricEventBody(BaseModel):
    """Eval metric event body."""
    suite_id: str = Field(..., alias="suiteId")
    metric: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    metadata: Optional[dict[str, Any]] = None


class CustomEventBody(BaseModel):
    """Custom event body for extensibility."""
    data: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Event Types
# =============================================================================

EventType = Literal[
    "log",
    "error", 
    "span",
    "token_usage",
    "message",
    "eval_metric",
    "agent_action",
    "retrieval",
    "tool_call",
    "model_response",
    "custom"
]

EventBody = Union[
    LogEventBody,
    ErrorEventBody,
    SpanEventBody,
    TokenUsageEventBody,
    MessageEventBody,
    ModelResponseEventBody,
    AgentActionEventBody,
    RetrievalEventBody,
    ToolCallEventBody,
    EvalMetricEventBody,
    CustomEventBody,
    dict[str, Any],  # Fallback for unknown types
]


# =============================================================================
# Main Event Envelope
# =============================================================================

class EventEnvelope(BaseModel):
    """
    Main event envelope that wraps all event types.
    This is what the SDK sends to the ingestion API.
    """
    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        alias="eventId",
        description="Unique event identifier"
    )
    project_id: str = Field(..., alias="projectId", description="Project identifier")
    type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp (ISO8601)"
    )
    sdk: SDKInfo = Field(..., description="SDK information")
    context: Optional[dict[str, Any]] = Field(None, description="Additional context")
    body: dict[str, Any] = Field(..., description="Event body (varies by type)")

    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


# =============================================================================
# API Response Models
# =============================================================================

class EventIngestResponse(BaseModel):
    """Response after successful event ingestion."""
    status: Literal["queued", "accepted"] = "queued"
    event_id: str = Field(..., alias="eventId")
    message: str = "Event received successfully"

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int

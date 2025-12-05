"""
Trace visualization routes.
Fetch and reconstruct trace hierarchies for visualization.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from schemas import ErrorResponse
import clickhouse as ch
from auth.supabase_middleware import require_user, User
from pydantic import BaseModel

logger = logging.getLogger("watchllm.query.traces")
router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class SpanData(BaseModel):
    event_id: str
    trace_id: str
    parent_event_id: Optional[str]
    type: str
    timestamp: datetime
    name: Optional[str] = None
    duration_ms: Optional[float] = None
    status: Optional[str] = None
    body: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    estimated_cost_usd: Optional[float] = None
    children: List['SpanData'] = []


class TraceResponse(BaseModel):
    trace_id: str
    project_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    total_events: int
    root_spans: List[SpanData]
    metadata: Dict[str, Any]


# Recursive model fix for Pydantic v2
SpanData.model_rebuild()


# =============================================================================
# Helper Functions
# =============================================================================

def build_trace_tree(events: List[Dict[str, Any]]) -> List[SpanData]:
    """Build hierarchical trace tree from flat event list."""
    
    # Create lookup dictionary
    events_by_id = {}
    for event in events:
        span = SpanData(
            event_id=event["event_id"],
            trace_id=event["trace_id"],
            parent_event_id=event.get("parent_event_id"),
            type=event["type"],
            timestamp=event["timestamp"] if isinstance(event["timestamp"], datetime) else datetime.fromisoformat(event["timestamp"]),
            name=event.get("body", {}).get("name") if isinstance(event.get("body"), dict) else None,
            duration_ms=event.get("body", {}).get("durationMs") if isinstance(event.get("body"), dict) else None,
            status=event.get("body", {}).get("status") if isinstance(event.get("body"), dict) else None,
            body=event.get("body", {}),
            context=event.get("context"),
            estimated_cost_usd=event.get("estimated_cost_usd"),
            children=[]
        )
        events_by_id[event["event_id"]] = span
    
    # Build tree structure
    roots = []
    for span in events_by_id.values():
        if span.parent_event_id and span.parent_event_id in events_by_id:
            # Has parent - add as child
            parent = events_by_id[span.parent_event_id]
            parent.children.append(span)
        else:
            # No parent or parent not in trace - root span
            roots.append(span)
    
    # Sort children by timestamp
    def sort_children(span: SpanData):
        span.children.sort(key=lambda x: x.timestamp)
        for child in span.children:
            sort_children(child)
    
    for root in roots:
        sort_children(root)
    
    return roots


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/traces/{trace_id}",
    response_model=TraceResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Trace not found"},
        503: {"model": ErrorResponse, "description": "Database unavailable"}
    }
)
async def get_trace(
    trace_id: str,
    project_id: str = Query(..., description="Project ID for authorization"),
    user: User = Depends(require_user),
):
    """
    Get a complete trace with all its spans in hierarchical structure.
    
    Returns all events for a given trace_id, organized as a tree based on
    parent_event_id relationships.
    """
    
    sql = """
    SELECT 
        event_id,
        project_id,
        trace_id,
        parent_event_id,
        type,
        timestamp,
        body,
        context,
        estimated_cost_usd
    FROM events
    WHERE trace_id = %(trace_id)s
      AND project_id = %(project_id)s
    ORDER BY timestamp ASC
    """
    
    params = {
        "trace_id": trace_id,
        "project_id": project_id
    }
    
    try:
        client = await ch.get_client()
        events = await client.query(sql, params)
        
        if not events:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Trace not found"}
            )
        
        # Calculate trace metadata
        start_time = min(e["timestamp"] if isinstance(e["timestamp"], datetime) else datetime.fromisoformat(e["timestamp"]) for e in events)
        end_time = max(e["timestamp"] if isinstance(e["timestamp"], datetime) else datetime.fromisoformat(e["timestamp"]) for e in events)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Build tree
        root_spans = build_trace_tree(events)
        
        # Extract metadata (from first event's context)
        metadata = {}
        if events and events[0].get("context"):
            ctx = events[0]["context"]
            if isinstance(ctx, dict):
                metadata = {
                    "user_id": ctx.get("userId"),
                    "session_id": ctx.get("sessionId"),
                    "environment": ctx.get("environment"),
                }
        
        return TraceResponse(
            trace_id=trace_id,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=round(duration_ms, 2),
            total_events=len(events),
            root_spans=root_spans,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )


@router.get("/traces", response_model=List[Dict[str, Any]])
async def list_traces(
    project_id: str = Query(..., description="Project ID"),
    limit: int = Query(50, ge=1, le=500, description="Max traces to return"),
    user: User = Depends(require_user),
):
    """
    List recent traces for a project.
    
    Returns a summary of traces with metadata for listing/search.
    """
    
    sql = """
    SELECT 
        trace_id,
        project_id,
        min(timestamp) as start_time,
        max(timestamp) as end_time,
        count() as event_count,
        sum(estimated_cost_usd) as total_cost,
        countIf(type = 'error') as error_count
    FROM events
    WHERE project_id = %(project_id)s
      AND trace_id != ''
    GROUP BY trace_id, project_id
    ORDER BY start_time DESC
    LIMIT %(limit)s
    """
    
    params = {
        "project_id": project_id,
        "limit": limit
    }
    
    try:
        client = await ch.get_client()
        result = await client.query(sql, params)
        
        traces = []
        for row in result:
            start = row["start_time"] if isinstance(row["start_time"], datetime) else datetime.fromisoformat(row["start_time"])
            end = row["end_time"] if isinstance(row["end_time"], datetime) else datetime.fromisoformat(row["end_time"])
            duration_ms = (end - start).total_seconds() * 1000
            
            traces.append({
                "trace_id": row["trace_id"],
                "project_id": row["project_id"],
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "duration_ms": round(duration_ms, 2),
                "event_count": row["event_count"],
                "total_cost": round(row.get("total_cost", 0), 6),
                "error_count": row["error_count"],
                "has_errors": row["error_count"] > 0
            })
        
        return traces
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )

"""
Event query routes.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from datetime import datetime, timedelta
import json
import logging

from schemas import EventResponse, EventListResponse, ErrorResponse
import clickhouse as ch

logger = logging.getLogger("lynex.query.events")
router = APIRouter()


@router.get(
    "/events",
    response_model=EventListResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Database unavailable"}
    }
)
async def list_events(
    project_id: str = Query(..., description="Project ID to filter by"),
    type: Optional[str] = Query(None, description="Event type filter"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
):
    """
    List events for a project with filters and pagination.
    
    **Filters:**
    - `project_id` (required): The project to query
    - `type`: Filter by event type (log, error, span, etc.)
    - `start_time`, `end_time`: Time range filter
    - `limit`, `offset`: Pagination
    """
    
    # Default to last 24 hours if no time filter
    if not start_time:
        start_time = datetime.utcnow() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.utcnow()
    
    # Build query
    where_clauses = [
        f"project_id = '{project_id}'",
        f"timestamp >= '{start_time.isoformat()}'",
        f"timestamp <= '{end_time.isoformat()}'",
    ]
    
    if type:
        where_clauses.append(f"type = '{type}'")
    
    where_sql = " AND ".join(where_clauses)
    
    # Count total
    count_sql = f"SELECT count() as total FROM events WHERE {where_sql}"
    
    # Get events
    events_sql = f"""
    SELECT 
        event_id,
        project_id,
        type,
        timestamp,
        sdk_name,
        sdk_version,
        body,
        context,
        estimated_cost_usd,
        queue_latency_ms
    FROM events
    WHERE {where_sql}
    ORDER BY timestamp DESC
    LIMIT {limit} OFFSET {offset}
    """
    
    try:
        client = await ch.get_client()
        
        # Execute both queries
        count_result = await client.query(count_sql)
        events_result = await client.query(events_sql)
        
        total = count_result[0]["total"] if count_result else 0
        
        events = []
        for row in events_result:
            events.append(EventResponse(
                event_id=row["event_id"],
                project_id=row["project_id"],
                type=row["type"],
                timestamp=row["timestamp"] if isinstance(row["timestamp"], datetime) else datetime.fromisoformat(row["timestamp"]),
                sdk_name=row["sdk_name"],
                sdk_version=row["sdk_version"],
                body=json.loads(row["body"]) if isinstance(row["body"], str) else row["body"],
                context=json.loads(row["context"]) if isinstance(row["context"], str) else row.get("context", {}),
                estimated_cost_usd=row.get("estimated_cost_usd", 0),
                queue_latency_ms=row.get("queue_latency_ms", 0),
            ))
        
        return EventListResponse(
            events=events,
            total=total,
            page=offset // limit + 1,
            page_size=limit,
            has_more=(offset + limit) < total,
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable", "detail": str(e)}
        )


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"}
    }
)
async def get_event(
    event_id: str,
    project_id: str = Query(..., description="Project ID"),
):
    """Get a single event by ID."""
    
    sql = f"""
    SELECT 
        event_id,
        project_id,
        type,
        timestamp,
        sdk_name,
        sdk_version,
        body,
        context,
        estimated_cost_usd,
        queue_latency_ms
    FROM events
    WHERE event_id = '{event_id}' AND project_id = '{project_id}'
    LIMIT 1
    """
    
    try:
        client = await ch.get_client()
        result = await client.query(sql)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Event not found"}
            )
        
        row = result[0]
        return EventResponse(
            event_id=row["event_id"],
            project_id=row["project_id"],
            type=row["type"],
            timestamp=row["timestamp"] if isinstance(row["timestamp"], datetime) else datetime.fromisoformat(row["timestamp"]),
            sdk_name=row["sdk_name"],
            sdk_version=row["sdk_version"],
            body=json.loads(row["body"]) if isinstance(row["body"], str) else row["body"],
            context=json.loads(row["context"]) if isinstance(row["context"], str) else row.get("context", {}),
            estimated_cost_usd=row.get("estimated_cost_usd", 0),
            queue_latency_ms=row.get("queue_latency_ms", 0),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )

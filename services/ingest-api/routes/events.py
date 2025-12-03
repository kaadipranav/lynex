"""
Event ingestion routes.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging

from schemas import EventEnvelope, EventIngestResponse, ErrorResponse
from auth import APIKeyData, get_api_key
import queue as event_queue


logger = logging.getLogger("sentryai.ingest.events")

router = APIRouter()


# =============================================================================
# Event Ingestion Endpoint
# =============================================================================

@router.post(
    "/events",
    response_model=EventIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Event accepted for processing"},
        400: {"model": ErrorResponse, "description": "Invalid event payload"},
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        422: {"description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Queue unavailable"},
    }
)
async def ingest_event(
    event: EventEnvelope,
    api_key: APIKeyData = Depends(get_api_key),
):
    """
    Ingest a single AI event.
    
    **Authentication Required:** Provide API key in `X-API-Key` header.
    
    Events are validated, enriched, and queued for processing.
    Returns 202 Accepted immediately (fire-and-forget).
    
    **Event Types:**
    - `log` - General log messages
    - `error` - Error events with stack traces
    - `span` - Tracing spans for model calls, tools, etc.
    - `token_usage` - Token consumption tracking
    - `message` - Prompts and responses
    - `model_response` - Full model call with latency
    - `agent_action` - Agent framework actions
    - `retrieval` - RAG retrieval events
    - `tool_call` - Tool/function calls
    - `eval_metric` - Evaluation metrics
    - `custom` - Custom events
    """
    
    # Log authenticated request
    logger.info(f"📥 Event received (auth: {api_key.project_id}):")
    logger.info(f"   ID: {event.event_id}")
    logger.info(f"   Project: {event.project_id}")
    logger.info(f"   Type: {event.type}")
    logger.info(f"   Timestamp: {event.timestamp}")
    logger.info(f"   SDK: {event.sdk.name} v{event.sdk.version}")
    
    # Warn if event project_id doesn't match API key project
    if event.project_id != api_key.project_id:
        logger.warning(
            f"Project mismatch: event={event.project_id}, key={api_key.project_id}"
        )
    
    # Push to Redis queue
    try:
        message_id = await event_queue.push_event(event)
        logger.info(f"   ✅ Queued: {message_id}")
    except Exception as e:
        logger.error(f"   ❌ Queue failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Queue unavailable",
                "message": "Event could not be queued. Please retry.",
            }
        )
    
    return EventIngestResponse(
        status="queued",
        event_id=event.event_id,
        message="Event received successfully"
    )


# =============================================================================
# Batch Ingestion Endpoint
# =============================================================================

@router.post(
    "/events/batch",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Batch accepted for processing"},
        401: {"model": ErrorResponse, "description": "Missing API key"},
        403: {"model": ErrorResponse, "description": "Invalid API key"},
        503: {"model": ErrorResponse, "description": "Queue unavailable"},
    }
)
async def ingest_events_batch(
    events: list[EventEnvelope],
    api_key: APIKeyData = Depends(get_api_key),
):
    """
    Ingest multiple events in a single request.
    
    **Authentication Required:** Provide API key in `X-API-Key` header.
    
    More efficient for SDKs that batch events.
    Maximum 100 events per batch.
    """
    
    if len(events) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 events per batch"
        )
    
    logger.info(f"📥 Batch received (auth: {api_key.project_id}): {len(events)} events")
    
    # Push all events to Redis queue
    try:
        message_ids = await event_queue.push_events_batch(events)
        logger.info(f"   ✅ Batch queued: {len(message_ids)} events")
    except Exception as e:
        logger.error(f"   ❌ Batch queue failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Queue unavailable",
                "message": "Events could not be queued. Please retry.",
            }
        )
    
    return {
        "status": "queued",
        "count": len(events),
        "event_ids": [e.event_id for e in events],
        "message": f"Batch of {len(events)} events queued"
    }

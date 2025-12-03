"""
Redis Queue Module.
Handles pushing events to Redis Streams for async processing.
"""

import json
import logging
from typing import Optional
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from config import settings
from schemas import EventEnvelope

logger = logging.getLogger("sentryai.ingest.queue")

# =============================================================================
# Redis Client Singleton
# =============================================================================

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    
    if _redis_client is None:
        logger.info(f"Connecting to Redis: {settings.redis_url[:30]}...")
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            _redis_client = None
            raise
    
    return _redis_client


async def close_redis_client():
    """Close Redis connection on shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


# =============================================================================
# Queue Constants
# =============================================================================

EVENTS_STREAM = "sentryai:events:incoming"
MAX_STREAM_LENGTH = 100000  # Trim stream to prevent unbounded growth


# =============================================================================
# Queue Operations
# =============================================================================

async def push_event(event: EventEnvelope) -> str:
    """
    Push a single event to the Redis Stream.
    
    Returns the stream message ID on success.
    Raises exception on failure.
    """
    client = await get_redis_client()
    
    # Serialize event to JSON
    event_data = {
        "event_id": event.event_id,
        "project_id": event.project_id,
        "type": event.type,
        "timestamp": event.timestamp.isoformat(),
        "sdk_name": event.sdk.name,
        "sdk_version": event.sdk.version,
        "body": json.dumps(event.body),
        "context": json.dumps(event.context) if event.context else "{}",
        "queued_at": datetime.utcnow().isoformat(),
    }
    
    try:
        # XADD to stream with auto-generated ID
        # MAXLEN ~ keeps stream size bounded (approximate trimming)
        message_id = await client.xadd(
            EVENTS_STREAM,
            event_data,
            maxlen=MAX_STREAM_LENGTH,
            approximate=True,
        )
        
        logger.debug(f"Event {event.event_id} queued with ID {message_id}")
        return message_id
        
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Redis error pushing event {event.event_id}: {e}")
        raise


async def push_events_batch(events: list[EventEnvelope]) -> list[str]:
    """
    Push multiple events to the Redis Stream.
    Uses pipeline for efficiency.
    
    Returns list of stream message IDs.
    """
    client = await get_redis_client()
    
    message_ids = []
    
    try:
        # Use pipeline for batch operations
        async with client.pipeline(transaction=False) as pipe:
            for event in events:
                event_data = {
                    "event_id": event.event_id,
                    "project_id": event.project_id,
                    "type": event.type,
                    "timestamp": event.timestamp.isoformat(),
                    "sdk_name": event.sdk.name,
                    "sdk_version": event.sdk.version,
                    "body": json.dumps(event.body),
                    "context": json.dumps(event.context) if event.context else "{}",
                    "queued_at": datetime.utcnow().isoformat(),
                }
                pipe.xadd(
                    EVENTS_STREAM,
                    event_data,
                    maxlen=MAX_STREAM_LENGTH,
                    approximate=True,
                )
            
            results = await pipe.execute()
            message_ids = [str(r) for r in results]
        
        logger.debug(f"Batch of {len(events)} events queued")
        return message_ids
        
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Redis error pushing batch: {e}")
        raise


async def get_queue_stats() -> dict:
    """Get queue statistics for monitoring."""
    try:
        client = await get_redis_client()
        
        # Get stream info
        info = await client.xinfo_stream(EVENTS_STREAM)
        
        return {
            "stream": EVENTS_STREAM,
            "length": info["length"],
            "first_entry": info.get("first-entry"),
            "last_entry": info.get("last-entry"),
            "groups": info.get("groups", 0),
        }
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return {
            "stream": EVENTS_STREAM,
            "error": str(e),
        }


async def health_check() -> bool:
    """Check if Redis is healthy."""
    try:
        client = await get_redis_client()
        await client.ping()
        return True
    except Exception:
        return False

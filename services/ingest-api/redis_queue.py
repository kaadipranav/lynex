"""
Redis Queue Module.
Handles pushing events to Redis Streams for async processing.
Supports in-memory fallback for local testing.
"""

import json
import logging
from typing import Optional
from datetime import datetime
from collections import deque
import uuid

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from config import settings
from schemas import EventEnvelope

logger = logging.getLogger("lynex.ingest.queue")

# =============================================================================
# In-Memory Queue Fallback (for testing without Redis)
# =============================================================================

_memory_queue: deque = deque(maxlen=10000)
_use_memory_queue = False


# =============================================================================
# Redis Client Singleton
# =============================================================================

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client singleton. Returns None if using memory queue."""
    global _redis_client, _use_memory_queue
    
    if _use_memory_queue:
        return None
    
    if _redis_client is None:
        logger.info(f"Connecting to Redis: {settings.redis_url[:40]}...")
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
            logger.info("📦 Falling back to in-memory queue")
            _redis_client = None
            _use_memory_queue = True
            return None
    
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

EVENTS_STREAM = "lynex:events:incoming"
MAX_STREAM_LENGTH = 100000  # Trim stream to prevent unbounded growth


# =============================================================================
# Queue Operations
# =============================================================================

async def push_event(event: EventEnvelope) -> str:
    """
    Push a single event to the Redis Stream (or memory queue as fallback).
    
    Returns the stream message ID on success.
    Raises exception on failure.
    """
    global _use_memory_queue
    
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
    
    # Memory queue fallback
    client = await get_redis_client()
    if client is None or _use_memory_queue:
        message_id = f"mem-{uuid.uuid4().hex[:12]}"
        _memory_queue.append({**event_data, "message_id": message_id})
        logger.debug(f"Event {event.event_id} queued to memory: {message_id}")
        return message_id
    
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
        # Fallback to memory queue on Redis failure
        _use_memory_queue = True
        message_id = f"mem-{uuid.uuid4().hex[:12]}"
        _memory_queue.append({**event_data, "message_id": message_id})
        logger.info(f"Event {event.event_id} queued to memory fallback: {message_id}")
        return message_id


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
    global _use_memory_queue
    
    if _use_memory_queue:
        return {
            "stream": "memory",
            "length": len(_memory_queue),
            "mode": "memory_fallback",
        }
    
    try:
        client = await get_redis_client()
        if client is None:
            return {
                "stream": "memory",
                "length": len(_memory_queue),
                "mode": "memory_fallback",
            }
        
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
    """Check if Redis is healthy (or memory queue is active)."""
    global _use_memory_queue
    
    if _use_memory_queue:
        return True  # Memory queue is always "healthy"
    
    try:
        client = await get_redis_client()
        if client is None:
            return True  # Memory fallback is healthy
        await client.ping()
        return True
    except Exception:
        return False


def get_memory_queue() -> list:
    """Get events from memory queue (for testing/debugging)."""
    return list(_memory_queue)

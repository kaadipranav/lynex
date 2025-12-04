"""
Redis Client Module.
"""

import redis.asyncio as redis
from config import settings

redis_client: redis.Redis = None

async def get_redis_client() -> redis.Redis:
    """Get or create a Redis client."""
    global redis_client
    if redis_client is None:
        # Use URL if available (DO App Platform), otherwise individual params
        if settings.redis_url:
            redis_client = redis.from_url(
                settings.redis_connection_url,
                decode_responses=True
            )
        else:
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
    return redis_client

async def close_redis_client():
    """Close the Redis client."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

"""
Redis Client Module.
"""

import logging
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings

logger = logging.getLogger("lynex.ui.redis")

redis_client: redis.Redis = None

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
    reraise=True
)
async def get_redis_client() -> redis.Redis:
    """Get or create a Redis client with retries."""
    global redis_client
    if redis_client is None:
        logger.info(f"Connecting to Redis...")
        redis_client = redis.from_url(
            settings.redis_connection_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
        )
        
        # Test connection
        await redis_client.ping()
        logger.info("✅ Redis connection established")
        
    return redis_client

async def close_redis_client():
    """Close the Redis client."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
        redis_client = None

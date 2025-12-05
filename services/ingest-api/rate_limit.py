"""
Rate Limiting Logic for Ingest API.
"""

import logging
from datetime import datetime
from models.subscription import SubscriptionTier, TIER_LIMITS
from redis_queue import get_redis_client

logger = logging.getLogger("watchllm.ingest.rate_limit")

TIER_KEY_PREFIX = "user:tier:"
USAGE_KEY_PREFIX = "user:usage:"

async def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limits.
    Returns True if allowed, False if limit exceeded.
    Increments usage if allowed.
    """
    redis = await get_redis_client()
    if not redis:
        # If Redis is down/memory mode, we can't enforce limits easily.
        # Fail open to ensure service continuity.
        return True

    try:
        # 1. Get Tier
        tier_value = await redis.get(f"{TIER_KEY_PREFIX}{user_id}")
        try:
            tier = SubscriptionTier(tier_value) if tier_value else SubscriptionTier.FREE
        except ValueError:
            tier = SubscriptionTier.FREE
        
        limit = TIER_LIMITS.get(tier, 10_000)
        if limit == float('inf'):
            return True

        # 2. Get Usage
        # Key format: user:usage:{user_id}:{YYYY-MM}
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage_key = f"{USAGE_KEY_PREFIX}{user_id}:{current_month}"
        
        # We use incr directly. It returns the new value.
        # If key doesn't exist, it sets to 0 then increments to 1.
        new_usage = await redis.incr(usage_key)
        
        # Set expiry if it's a new key (value is 1)
        if new_usage == 1:
             await redis.expire(usage_key, 60*60*24*32) # 32 days

        # Check if we exceeded limit
        if new_usage > limit:
            return False
        
        return True

    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open on error
        return True

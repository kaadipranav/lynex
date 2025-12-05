"""
Rate Limiting and Subscription Logic.
"""

import logging
from typing import Optional

from models.subscription import SubscriptionTier, TIER_LIMITS
from redis_client import get_redis_client

logger = logging.getLogger("watchllm.rate_limit")

TIER_KEY_PREFIX = "user:tier:"
USAGE_KEY_PREFIX = "user:usage:"

async def get_user_tier(user_id: str) -> SubscriptionTier:
    """Get the subscription tier for a user from Redis."""
    try:
        redis = await get_redis_client()
        tier_value = await redis.get(f"{TIER_KEY_PREFIX}{user_id}")
        if tier_value:
            try:
                return SubscriptionTier(tier_value)
            except ValueError:
                logger.warning(f"Invalid tier value in Redis for user {user_id}: {tier_value}")
                return SubscriptionTier.FREE
        return SubscriptionTier.FREE
    except Exception as e:
        logger.error(f"Error fetching tier from Redis: {e}")
        # Fallback to FREE on error
        return SubscriptionTier.FREE

async def get_user_usage(user_id: str) -> int:
    """Get the current month's usage for a user from Redis."""
    try:
        redis = await get_redis_client()
        from datetime import datetime
        current_month = datetime.utcnow().strftime("%Y-%m")
        usage_key = f"{USAGE_KEY_PREFIX}{user_id}:{current_month}"
        usage = await redis.get(usage_key)
        return int(usage) if usage else 0
    except Exception as e:
        logger.error(f"Error fetching usage from Redis: {e}")
        return 0

async def set_user_tier(user_id: str, tier: SubscriptionTier):
    """Set the subscription tier for a user in Redis."""
    try:
        redis = await get_redis_client()
        await redis.set(f"{TIER_KEY_PREFIX}{user_id}", tier.value)
        logger.info(f"Set tier for user {user_id} to {tier.value}")
    except Exception as e:
        logger.error(f"Error setting tier in Redis: {e}")
        raise

def get_tier_limit(tier: SubscriptionTier) -> int:
    """Get the monthly event limit for a tier."""
    return TIER_LIMITS.get(tier, 10_000)

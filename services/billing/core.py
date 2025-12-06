"""
Billing Service with Whop Integration.
Handles subscription tiers, usage tracking, and payment webhooks.
"""

import logging
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

import httpx
from shared.database import get_db

logger = logging.getLogger("watchllm.billing")


# =============================================================================
# Subscription Tiers
# =============================================================================

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "events_per_month": 50_000,
        "retention_days": 7,
        "projects": 1,
        "team_members": 1,
        "alerts": 3,
    },
    SubscriptionTier.PRO: {
        "events_per_month": 500_000,
        "retention_days": 30,
        "projects": 5,
        "team_members": 5,
        "alerts": 20,
    },
    SubscriptionTier.BUSINESS: {
        "events_per_month": 5_000_000,
        "retention_days": 90,
        "projects": -1,  # Unlimited
        "team_members": -1,
        "alerts": -1,
    },
}


# =============================================================================
# Models
# =============================================================================

class Subscription(BaseModel):
    user_id: str
    tier: SubscriptionTier
    whop_membership_id: Optional[str] = None
    whop_plan_id: Optional[str] = None
    status: str = "active"  # active, canceled, past_due
    current_period_start: datetime
    current_period_end: datetime
    events_used_this_period: int = 0


class UsageRecord(BaseModel):
    user_id: str
    project_id: str
    event_count: int
    timestamp: datetime


# =============================================================================
# Database Operations
# =============================================================================

async def get_subscription(user_id: str) -> Subscription:
    """Get subscription for a user, creating default FREE tier if none exists."""
    db = await get_db()
    sub_doc = await db.subscriptions.find_one({"user_id": user_id})
    
    now = datetime.utcnow()
    
    if not sub_doc:
        # Create default free subscription
        # End date is 1 month from now for free tier
        end_date = now + timedelta(days=30)
        
        sub_doc = {
            "user_id": user_id,
            "tier": SubscriptionTier.FREE,
            "whop_membership_id": None,
            "whop_plan_id": None,
            "status": "active",
            "current_period_start": now,
            "current_period_end": end_date,
            "events_used_this_period": 0,
        }
        await db.subscriptions.insert_one(sub_doc)
    
    # Check for period reset (Lazy check)
    # If current time is past period end, reset usage and update period
    # This is critical for Free tier auto-renewal
    current_end = sub_doc.get("current_period_end")
    if isinstance(current_end, str):
        current_end = datetime.fromisoformat(current_end)
        
    if current_end and now > current_end:
        # If it's a free tier, auto-renew
        if sub_doc.get("tier") == SubscriptionTier.FREE:
            new_start = now
            new_end = now + timedelta(days=30)
            
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "current_period_start": new_start,
                        "current_period_end": new_end,
                        "events_used_this_period": 0
                    }
                }
            )
            # Update local doc
            sub_doc["current_period_start"] = new_start
            sub_doc["current_period_end"] = new_end
            sub_doc["events_used_this_period"] = 0
            logger.info(f"Auto-renewed free subscription for {user_id}")
            
        # For paid tiers, we usually wait for webhook, but if it's way past due,
        # we might want to reset usage anyway if we assume they are still active?
        # For now, let's only auto-renew Free tier to avoid conflicts with Whop.
        
    return Subscription(**sub_doc)


async def update_usage(user_id: str, event_count: int = 1):
    """Increment usage for the current period."""
    db = await get_db()
    await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$inc": {"events_used_this_period": event_count}}
    )


# =============================================================================
# Whop API Client
# =============================================================================


class WhopClient:
    """Client for Whop API interactions."""
    
    BASE_URL = "https://api.whop.com/api/v2"
    
    def __init__(self, api_key: str, webhook_secret: str = ""):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    async def get_membership(self, membership_id: str) -> Optional[dict]:
        """Get membership details from Whop."""
        try:
            response = await self.client.get(f"/memberships/{membership_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Whop API error: {e}")
            return None
    
    async def validate_license_key(self, license_key: str) -> Optional[dict]:
        """Validate a Whop license key."""
        try:
            response = await self.client.post(
                "/memberships/validate_license",
                json={"license_key": license_key}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Whop license validation error: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Whop webhook signature."""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return True  # Skip verification in dev
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)


def get_whop_client(api_key: str, webhook_secret: str = "") -> WhopClient:
    """Get a WhopClient instance."""
    return WhopClient(api_key, webhook_secret)


# =============================================================================
# Plan Mapping
# =============================================================================

def map_whop_plan_to_tier(plan_id: str) -> SubscriptionTier:
    """Map Whop plan ID to subscription tier."""
    # Configure these with your actual Whop plan IDs
    PLAN_MAPPING = {
        "plan_pro_monthly": SubscriptionTier.PRO,
        "plan_pro_yearly": SubscriptionTier.PRO,
        "plan_business_monthly": SubscriptionTier.BUSINESS,
        "plan_business_yearly": SubscriptionTier.BUSINESS,
    }
    return PLAN_MAPPING.get(plan_id, SubscriptionTier.FREE)


async def update_subscription_from_whop(user_id: str, membership_data: dict):
    """Update subscription based on Whop membership data."""
    db = await get_db()
    
    # Map Whop plan to our tier
    plan_id = membership_data.get("plan", {}).get("id", "")
    tier = map_whop_plan_to_tier(plan_id)
    
    new_start = datetime.fromisoformat(membership_data.get("renewal_period_start", datetime.utcnow().isoformat()))
    new_end = datetime.fromisoformat(membership_data.get("renewal_period_end", datetime.utcnow().isoformat()))
    
    # Check if we need to reset usage (new period)
    # We fetch existing to compare
    existing = await db.subscriptions.find_one({"user_id": user_id})
    reset_usage = False
    if existing:
        old_start = existing.get("current_period_start")
        # If start date changed significantly (more than a day), it's a new period
        if old_start and abs((new_start - old_start).total_seconds()) > 86400:
            reset_usage = True
    
    update_data = {
        "tier": tier,
        "whop_membership_id": membership_data.get("id"),
        "whop_plan_id": plan_id,
        "status": "active" if membership_data.get("valid") else "canceled",
        "current_period_start": new_start,
        "current_period_end": new_end,
    }
    
    if reset_usage:
        update_data["events_used_this_period"] = 0
        logger.info(f"Resetting usage for {user_id} due to new billing period")
    
    await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )
    
    logger.info(f"Updated subscription for {user_id}: {tier}")


# =============================================================================
# Usage Tracking
# =============================================================================

async def check_usage_limit(user_id: str) -> tuple[bool, dict]:
    """Check if user is within their usage limits."""
    
    sub = await get_subscription(user_id)
    limits = TIER_LIMITS[sub.tier]
    
    events_limit = limits["events_per_month"]
    events_used = sub.events_used_this_period
    
    # -1 means unlimited
    if events_limit == -1:
        return True, {"allowed": True, "used": events_used, "limit": "unlimited"}
    
    allowed = events_used < events_limit
    
    return allowed, {
        "allowed": allowed,
        "used": events_used,
        "limit": events_limit,
        "remaining": max(0, events_limit - events_used),
        "percentage": round(events_used / events_limit * 100, 1),
    }


async def get_usage_stats(user_id: str) -> dict:
    """Get usage statistics for a user."""
    
    sub = await get_subscription(user_id)
    limits = TIER_LIMITS[sub.tier]
    
    allowed, usage_info = await check_usage_limit(user_id)
    
    return {
        "subscription": {
            "tier": sub.tier.value,
            "status": sub.status,
            "period_start": sub.current_period_start.isoformat(),
            "period_end": sub.current_period_end.isoformat(),
        },
        "usage": usage_info,
        "limits": limits,
    }

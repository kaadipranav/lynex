"""
Billing API Routes.
"""

import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).resolve().parent.parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from fastapi import APIRouter, HTTPException, Request, Header, status
from pydantic import BaseModel
from typing import Optional
import logging

from billing import (
    get_subscription,
    get_usage_stats,
    check_usage_limit,
    update_subscription_from_whop,
    get_whop_client,
    Subscription,
    SubscriptionTier,
    TIER_LIMITS,
)
from config import settings

logger = logging.getLogger("watchllm.billing.routes")
router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class ActivateLicenseRequest(BaseModel):
    license_key: str


class UsageResponse(BaseModel):
    subscription: dict
    usage: dict
    limits: dict


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/billing/subscription")
async def get_user_subscription(user_id: str):
    """Get current subscription for a user."""
    sub = await get_subscription(user_id)
    limits = TIER_LIMITS[sub.tier]
    
    return {
        "subscription": sub.dict(),
        "limits": limits,
        "usage_pct": (sub.events_used_this_period / limits["events_per_month"]) * 100
    }


@router.get("/billing/usage")
async def get_user_usage(user_id: str):
    """Get usage statistics for a user."""
    return await get_usage_stats(user_id)


@router.get("/billing/check-limit")
async def check_user_limit(user_id: str):
    """Check if user can send more events."""
    allowed, info = await check_usage_limit(user_id)
    
    if not allowed:
        return {
            "allowed": False,
            "message": "Event limit reached. Please upgrade your plan.",
            **info,
        }
    
    return {"allowed": True, **info}


@router.post("/billing/activate-license")
async def activate_license(user_id: str, data: ActivateLicenseRequest):
    """Activate a Whop license key for a user."""
    
    client = get_whop_client(settings.whop_api_key, settings.whop_webhook_secret)
    
    # Validate license with Whop
    membership = await client.validate_license_key(data.license_key)
    
    if not membership or not membership.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired license key"
        )
    
    # Update subscription
    await update_subscription_from_whop(user_id, membership)
    
    return {
        "success": True,
        "message": "License activated successfully",
        "subscription": (await get_subscription(user_id)).dict(),
    }


@router.get("/billing/plans")
async def get_available_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "interval": "month",
                "features": TIER_LIMITS[SubscriptionTier.FREE],
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29,
                "interval": "month",
                "features": TIER_LIMITS[SubscriptionTier.PRO],
                "whop_url": "https://whop.com/your-product/pro",  # Replace with actual
            },
            {
                "id": "business",
                "name": "Business",
                "price": 99,
                "interval": "month",
                "features": TIER_LIMITS[SubscriptionTier.BUSINESS],
                "whop_url": "https://whop.com/your-product/business",  # Replace with actual
            },
        ]
    }


# =============================================================================
# Whop Webhook Handler
# =============================================================================

@router.post("/billing/webhooks/whop")
async def whop_webhook(
    request: Request,
    x_whop_signature: Optional[str] = Header(None),
):
    """Handle Whop webhook events."""
    
    body = await request.body()
    
    # Verify signature
    client = get_whop_client(settings.whop_api_key, settings.whop_webhook_secret)
    if x_whop_signature and not client.verify_webhook_signature(body, x_whop_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    payload = await request.json()
    event_type = payload.get("action")
    data = payload.get("data", {})
    
    logger.info(f"Whop webhook: {event_type}")
    
    # Handle different event types
    if event_type == "membership.went_valid":
        # New subscription or renewal
        user_id = data.get("metadata", {}).get("user_id")
        if user_id:
            await update_subscription_from_whop(user_id, data)
    
    elif event_type == "membership.went_invalid":
        # Subscription canceled or expired
        user_id = data.get("metadata", {}).get("user_id")
        if user_id:
            from shared.database import get_db
            db = await get_db()
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {"status": "canceled", "tier": SubscriptionTier.FREE}}
            )
    
    elif event_type == "payment.succeeded":
    elif event_type == "payment.failed":
        logger.warning(f"Payment failed: {data.get('id')}")
        user_id = data.get("membership", {}).get("metadata", {}).get("user_id")
        if user_id:
            from shared.database import get_db
            db = await get_db()
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {"status": "past_due"}}
            )
    
    return {"received": True}[user_id]["status"] = "past_due"
    
    return {"received": True}

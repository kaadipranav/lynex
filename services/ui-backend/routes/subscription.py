from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated

from auth.supabase_middleware import require_user, User
from middleware.rate_limit import get_user_tier, get_user_usage, get_tier_limit
from models.subscription import SubscriptionTier

router = APIRouter(prefix="/subscription", tags=["Subscription"])

class UsageResponse(BaseModel):
    tier: SubscriptionTier
    usage: int
    limit: int
    percent_used: float

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    user: User = Depends(require_user)
):
    """
    Get current subscription usage.
    """
    user_id = user.id
    
    tier = await get_user_tier(user_id)
    usage = await get_user_usage(user_id)
    limit = get_tier_limit(tier)
    
    percent = 0.0
    if limit > 0 and limit != float('inf'):
        percent = (usage / limit) * 100
    elif limit == float('inf'):
        percent = 0.0 # Or maybe 0?
        
    return UsageResponse(
        tier=tier,
        usage=usage,
        limit=limit if limit != float('inf') else -1, # -1 for unlimited in JSON
        percent_used=percent
    )

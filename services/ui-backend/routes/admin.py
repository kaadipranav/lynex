from fastapi import APIRouter, HTTPException, Header, Depends, Body
from pydantic import BaseModel
from typing import Annotated

from config import settings
from models.subscription import SubscriptionTier
from middleware.rate_limit import set_user_tier

router = APIRouter(prefix="/admin", tags=["Admin"])

class UpgradeUserRequest(BaseModel):
    user_id: str
    tier: SubscriptionTier

async def verify_admin_key(x_admin_api_key: Annotated[str, Header()] = None):
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid Admin API Key")
    return x_admin_api_key

@router.post("/upgrade-user")
async def upgrade_user(
    request: UpgradeUserRequest,
    _: str = Depends(verify_admin_key)
):
    """
    Manually upgrade a user's tier.
    Requires 'x-admin-api-key' header.
    """
    try:
        await set_user_tier(request.user_id, request.tier)
        return {"status": "success", "message": f"User {request.user_id} upgraded to {request.tier.value}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

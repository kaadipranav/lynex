"""
Subscription Models.
"""

from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Subscription(BaseModel):
    user_id: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    current_period_start: datetime
    current_period_end: datetime
    event_count: int = 0
    limit: int

    @property
    def is_over_limit(self) -> bool:
        if self.tier == SubscriptionTier.ENTERPRISE:
            return False
        return self.event_count >= self.limit

TIER_LIMITS = {
    SubscriptionTier.FREE: 10_000,
    SubscriptionTier.PRO: 100_000,
    SubscriptionTier.ENTERPRISE: float('inf'),
}

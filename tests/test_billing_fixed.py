"""
Unit tests for fixed billing service.
Tests the fixes for duplicate functions, webhook signature verification, and plan mapping.
"""

import pytest
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add billing service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "billing"))

from billing import (
    SubscriptionTier,
    TIER_LIMITS,
    get_subscription,
    update_usage,
    map_whop_plan_to_tier,
    update_subscription_from_whop,
    check_usage_limit,
    get_usage_stats,
    WhopClient,
)


@pytest.mark.unit
class TestWhopPlanMapping:
    """Test Whop plan ID to tier mapping."""
    
    def test_map_pro_monthly(self):
        """Test PRO monthly plan mapping."""
        tier = map_whop_plan_to_tier("plan_pro_monthly")
        assert tier == SubscriptionTier.PRO
    
    def test_map_pro_yearly(self):
        """Test PRO yearly plan mapping."""
        tier = map_whop_plan_to_tier("plan_pro_yearly")
        assert tier == SubscriptionTier.PRO
    
    def test_map_business_monthly(self):
        """Test BUSINESS monthly plan mapping."""
        tier = map_whop_plan_to_tier("plan_business_monthly")
        assert tier == SubscriptionTier.BUSINESS
    
    def test_map_business_yearly(self):
        """Test BUSINESS yearly plan mapping."""
        tier = map_whop_plan_to_tier("plan_business_yearly")
        assert tier == SubscriptionTier.BUSINESS
    
    def test_map_unknown_defaults_to_free(self):
        """Test unknown plan ID defaults to FREE tier."""
        tier = map_whop_plan_to_tier("unknown_plan")
        assert tier == SubscriptionTier.FREE
    
    def test_map_empty_string_defaults_to_free(self):
        """Test empty plan ID defaults to FREE tier."""
        tier = map_whop_plan_to_tier("")
        assert tier == SubscriptionTier.FREE


@pytest.mark.unit
class TestWhopWebhookSignature:
    """Test Whop webhook signature verification."""
    
    def test_verify_valid_signature(self):
        """Test verification of valid webhook signature."""
        secret = "test_webhook_secret"
        payload = b'{"event": "membership.created"}'
        
        # Generate valid signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        client = WhopClient(api_key="test_key", webhook_secret=secret)
        is_valid = client.verify_webhook_signature(payload, expected_signature)
        
        assert is_valid is True
    
    def test_verify_invalid_signature(self):
        """Test rejection of invalid webhook signature."""
        secret = "test_webhook_secret"
        payload = b'{"event": "membership.created"}'
        invalid_signature = "invalid_signature_hash"
        
        client = WhopClient(api_key="test_key", webhook_secret=secret)
        is_valid = client.verify_webhook_signature(payload, invalid_signature)
        
        assert is_valid is False
    
    def test_verify_without_secret_skips_verification(self):
        """Test that missing webhook secret skips verification (dev mode)."""
        payload = b'{"event": "membership.created"}'
        
        client = WhopClient(api_key="test_key", webhook_secret="")
        is_valid = client.verify_webhook_signature(payload, "any_signature")
        
        # Should return True in dev mode (no secret configured)
        assert is_valid is True
    
    def test_verify_tampered_payload(self):
        """Test rejection of tampered payload."""
        secret = "test_webhook_secret"
        original_payload = b'{"event": "membership.created"}'
        tampered_payload = b'{"event": "membership.deleted"}'
        
        # Generate signature for original payload
        signature = hmac.new(
            secret.encode(),
            original_payload,
            hashlib.sha256
        ).hexdigest()
        
        # Try to verify with tampered payload
        client = WhopClient(api_key="test_key", webhook_secret=secret)
        is_valid = client.verify_webhook_signature(tampered_payload, signature)
        
        assert is_valid is False


@pytest.mark.unit
class TestSubscriptionAutoRenewal:
    """Test free tier auto-renewal logic."""
    
    @pytest.mark.asyncio
    async def test_free_tier_auto_renews_after_period_end(self, mock_mongodb):
        """Test that free tier auto-renews when period ends."""
        now = datetime.utcnow()
        past_end = now - timedelta(days=1)
        
        # Mock existing free subscription with expired period
        mock_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.FREE,
            "current_period_start": now - timedelta(days=31),
            "current_period_end": past_end,
            "events_used_this_period": 40000,
            "status": "active",
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=mock_sub)
        mock_db.subscriptions.update_one = AsyncMock()
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            result = await get_subscription("test-user")
            
            # Should have called update to reset usage and extend period
            mock_db.subscriptions.update_one.assert_called_once()
            call_args = mock_db.subscriptions.update_one.call_args
            
            # Verify reset happened
            assert call_args[0][1]["$set"]["events_used_this_period"] == 0
    
    @pytest.mark.asyncio
    async def test_free_tier_no_renewal_within_period(self, mock_mongodb):
        """Test that free tier does NOT renew within active period."""
        now = datetime.utcnow()
        future_end = now + timedelta(days=15)
        
        mock_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.FREE,
            "current_period_start": now - timedelta(days=15),
            "current_period_end": future_end,
            "events_used_this_period": 20000,
            "status": "active",
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=mock_sub)
        mock_db.subscriptions.update_one = AsyncMock()
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            result = await get_subscription("test-user")
            
            # Should NOT have called update (period still active)
            mock_db.subscriptions.update_one.assert_not_called()


@pytest.mark.unit
class TestUsageLimitChecks:
    """Test usage limit checking logic."""
    
    @pytest.mark.asyncio
    async def test_free_tier_under_limit(self, mock_mongodb):
        """Test FREE tier user under limit."""
        mock_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.FREE,
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(days=30),
            "events_used_this_period": 25000,  # Under 50K limit
            "status": "active",
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=mock_sub)
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            allowed, info = await check_usage_limit("test-user")
            
            assert allowed is True
            assert info["allowed"] is True
            assert info["used"] == 25000
            assert info["limit"] == 50000
            assert info["remaining"] == 25000
    
    @pytest.mark.asyncio
    async def test_free_tier_over_limit(self, mock_mongodb):
        """Test FREE tier user over limit."""
        mock_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.FREE,
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(days=30),
            "events_used_this_period": 55000,  # Over 50K limit
            "status": "active",
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=mock_sub)
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            allowed, info = await check_usage_limit("test-user")
            
            assert allowed is False
            assert info["allowed"] is False
            assert info["used"] == 55000
            assert info["limit"] == 50000
            assert info["remaining"] == 0
    
    @pytest.mark.asyncio
    async def test_business_tier_unlimited(self, mock_mongodb):
        """Test BUSINESS tier has unlimited events."""
        mock_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.BUSINESS,
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(days=30),
            "events_used_this_period": 10_000_000,  # 10M events
            "status": "active",
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=mock_sub)
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            allowed, info = await check_usage_limit("test-user")
            
            assert allowed is True
            assert info["allowed"] is True
            assert info["limit"] == "unlimited"


@pytest.mark.unit
class TestWhopSubscriptionUpdate:
    """Test Whop subscription update logic."""
    
    @pytest.mark.asyncio
    async def test_update_from_whop_new_period_resets_usage(self, mock_mongodb):
        """Test that new billing period resets usage."""
        now = datetime.utcnow()
        old_start = now - timedelta(days=60)
        new_start = now
        
        # Existing subscription with old period
        existing_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.PRO,
            "current_period_start": old_start,
            "events_used_this_period": 400000,
        }
        
        # New Whop membership data
        membership_data = {
            "id": "mem_123",
            "plan": {"id": "plan_pro_monthly"},
            "valid": True,
            "renewal_period_start": new_start.isoformat(),
            "renewal_period_end": (new_start + timedelta(days=30)).isoformat(),
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=existing_sub)
        mock_db.subscriptions.update_one = AsyncMock()
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            await update_subscription_from_whop("test-user", membership_data)
            
            # Should have reset usage
            call_args = mock_db.subscriptions.update_one.call_args
            update_data = call_args[0][1]["$set"]
            assert update_data["events_used_this_period"] == 0
    
    @pytest.mark.asyncio
    async def test_update_from_whop_same_period_keeps_usage(self, mock_mongodb):
        """Test that same billing period keeps existing usage."""
        now = datetime.utcnow()
        period_start = now - timedelta(hours=12)  # Same day
        
        existing_sub = {
            "user_id": "test-user",
            "tier": SubscriptionTier.PRO,
            "current_period_start": period_start,
            "events_used_this_period": 100000,
        }
        
        membership_data = {
            "id": "mem_123",
            "plan": {"id": "plan_pro_monthly"},
            "valid": True,
            "renewal_period_start": period_start.isoformat(),
            "renewal_period_end": (period_start + timedelta(days=30)).isoformat(),
        }
        
        mock_db = MagicMock()
        mock_db.subscriptions.find_one = AsyncMock(return_value=existing_sub)
        mock_db.subscriptions.update_one = AsyncMock()
        
        with patch("billing.get_db", AsyncMock(return_value=mock_db)):
            await update_subscription_from_whop("test-user", membership_data)
            
            # Should NOT have reset usage
            call_args = mock_db.subscriptions.update_one.call_args
            update_data = call_args[0][1]["$set"]
            assert "events_used_this_period" not in update_data


@pytest.mark.unit
class TestTierLimits:
    """Test tier limit constants."""
    
    def test_free_tier_limits(self):
        """Test FREE tier limits."""
        limits = TIER_LIMITS[SubscriptionTier.FREE]
        assert limits["events_per_month"] == 50_000
        assert limits["retention_days"] == 7
        assert limits["projects"] == 1
        assert limits["team_members"] == 1
        assert limits["alerts"] == 3
    
    def test_pro_tier_limits(self):
        """Test PRO tier limits."""
        limits = TIER_LIMITS[SubscriptionTier.PRO]
        assert limits["events_per_month"] == 500_000
        assert limits["retention_days"] == 30
        assert limits["projects"] == 5
        assert limits["team_members"] == 5
        assert limits["alerts"] == 20
    
    def test_business_tier_unlimited(self):
        """Test BUSINESS tier unlimited features."""
        limits = TIER_LIMITS[SubscriptionTier.BUSINESS]
        assert limits["events_per_month"] == 5_000_000
        assert limits["retention_days"] == 90
        assert limits["projects"] == -1  # Unlimited
        assert limits["team_members"] == -1  # Unlimited
        assert limits["alerts"] == -1  # Unlimited

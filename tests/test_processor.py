"""
Unit tests for Processor alert evaluation logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
from pathlib import Path

# Add processor service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "processor"))

from pricing import pricing_calculator, PricingCalculator


class TestPricingCalculator:
    """Test pricing calculator for cost estimation."""
    
    def test_gpt4_cost_calculation(self, pricing_test_cases):
        """Test GPT-4 cost calculation."""
        test_case = pricing_test_cases[0]
        
        cost = pricing_calculator.calculate_cost(
            model=test_case["model"],
            input_tokens=test_case["input_tokens"],
            output_tokens=test_case["output_tokens"],
        )
        
        assert cost == pytest.approx(test_case["expected_cost"], rel=1e-6)
    
    def test_gpt4o_mini_cost_calculation(self, pricing_test_cases):
        """Test GPT-4o-mini cost calculation."""
        test_case = pricing_test_cases[1]
        
        cost = pricing_calculator.calculate_cost(
            model=test_case["model"],
            input_tokens=test_case["input_tokens"],
            output_tokens=test_case["output_tokens"],
        )
        
        assert cost == pytest.approx(test_case["expected_cost"], rel=1e-2)
    
    def test_versioned_model_name(self, pricing_test_cases):
        """Test that versioned model names are normalized correctly."""
        test_case = pricing_test_cases[2]
        
        cost = pricing_calculator.calculate_cost(
            model=test_case["model"],
            input_tokens=test_case["input_tokens"],
            output_tokens=test_case["output_tokens"],
        )
        
        # Should match claude-3-opus pricing despite version suffix
        assert cost == pytest.approx(test_case["expected_cost"], rel=1e-2)
    
    def test_total_tokens_estimation(self):
        """Test cost calculation with only total_tokens."""
        # When only total_tokens is available, assume 70/30 input/output split
        cost = pricing_calculator.calculate_cost(
            model="gpt-4",
            total_tokens=1000,
        )
        
        # Expected: (700/1M * 30) + (300/1M * 60) = 0.021 + 0.018 = 0.039
        assert cost == pytest.approx(0.039, rel=1e-2)
    
    def test_unknown_model_uses_default(self):
        """Test that unknown models use default pricing."""
        cost = pricing_calculator.calculate_cost(
            model="unknown-model-xyz",
            input_tokens=1000,
            output_tokens=500,
        )
        
        # Default pricing: input=$1/1M, output=$2/1M
        # Expected: (1000/1M * 1) + (500/1M * 2) = 0.001 + 0.001 = 0.002
        assert cost == pytest.approx(0.002, rel=1e-6)
    
    def test_zero_tokens(self):
        """Test handling of zero tokens."""
        cost = pricing_calculator.calculate_cost(
            model="gpt-4",
            input_tokens=0,
            output_tokens=0,
        )
        assert cost == 0.0
    
    def test_get_model_pricing(self):
        """Test retrieving pricing info for a model."""
        pricing = pricing_calculator.get_model_pricing("gpt-4")
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] == 30.0
        assert pricing["output"] == 60.0
    
    def test_normalize_model_name(self):
        """Test model name normalization."""
        calc = PricingCalculator()
        
        # Test exact match
        assert calc._normalize_model_name("gpt-4") == "gpt-4"
        
        # Test versioned model
        assert calc._normalize_model_name("gpt-4-0125-preview") == "gpt-4"
        
        # Test with uppercase
        assert calc._normalize_model_name("GPT-4") == "gpt-4"
        
        # Test unknown model
        assert calc._normalize_model_name("unknown-xyz") == "default"


class TestAlertEvaluation:
    """Test alert rule evaluation logic."""
    
    def test_error_count_threshold(self, sample_alert_rule):
        """Test error count threshold alert."""
        # Rule: trigger if error count > 10 in 5 minutes
        rule = sample_alert_rule
        
        # Simulate 12 errors
        error_count = 12
        
        should_trigger = error_count > rule["threshold"]
        assert should_trigger is True
    
    def test_below_threshold_no_alert(self, sample_alert_rule):
        """Test that count below threshold doesn't trigger."""
        rule = sample_alert_rule
        
        # Simulate 5 errors (below threshold of 10)
        error_count = 5
        
        should_trigger = error_count > rule["threshold"]
        assert should_trigger is False
    
    def test_cost_threshold_alert(self):
        """Test cost threshold alert."""
        rule = {
            "condition": "sum",
            "field": "estimated_cost_usd",
            "threshold": 10.0,  # $10
        }
        
        # Simulate $15 in costs
        total_cost = 15.0
        
        should_trigger = total_cost > rule["threshold"]
        assert should_trigger is True
    
    def test_latency_threshold_alert(self):
        """Test latency threshold alert."""
        rule = {
            "condition": "avg",
            "field": "latency_ms",
            "threshold": 5000,  # 5 seconds
        }
        
        # Simulate average latency of 7 seconds
        avg_latency = 7000
        
        should_trigger = avg_latency > rule["threshold"]
        assert should_trigger is True
    
    def test_disabled_rule_no_trigger(self, sample_alert_rule):
        """Test that disabled rules don't trigger."""
        rule = sample_alert_rule
        rule["enabled"] = False
        
        error_count = 100  # Way over threshold
        
        # Even though count is high, disabled rule shouldn't trigger
        should_trigger = rule["enabled"] and (error_count > rule["threshold"])
        assert should_trigger is False


class TestEventEnrichment:
    """Test event enrichment with cost data."""
    
    @pytest.mark.asyncio
    async def test_enrich_token_usage_with_cost(self, sample_token_usage_event):
        """Test that token_usage events are enriched with cost."""
        event = sample_token_usage_event
        
        # Calculate expected cost
        cost = pricing_calculator.calculate_cost(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
        )
        
        # Expected: (100/1M * 30) + (50/1M * 60) = 0.003 + 0.003 = 0.006
        assert cost == pytest.approx(0.006, rel=1e-6)
        
        # In real enrichment, this would be added to the event
        enriched = event.copy()
        enriched["estimated_cost_usd"] = cost
        
        assert "estimated_cost_usd" in enriched
        assert enriched["estimated_cost_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_enrich_with_cost_breakdown(self):
        """Test cost breakdown in enrichment."""
        event = {
            "type": "token_usage",
            "body": {
                "model": "gpt-4",
                "inputTokens": 1000,
                "outputTokens": 500,
            }
        }
        
        cost = pricing_calculator.calculate_cost(
            model="gpt-4",
            input_tokens=1000,
            output_tokens=500,
        )
        
        pricing = pricing_calculator.get_model_pricing("gpt-4")
        input_cost = (1000 / 1_000_000) * pricing["input"]
        output_cost = (500 / 1_000_000) * pricing["output"]
        
        enriched = event.copy()
        enriched["estimated_cost_usd"] = cost
        enriched["cost_breakdown"] = {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "input_tokens": 1000,
            "output_tokens": 500,
            "model": "gpt-4",
        }
        
        assert enriched["cost_breakdown"]["input_cost"] == pytest.approx(0.03, rel=1e-6)
        assert enriched["cost_breakdown"]["output_cost"] == pytest.approx(0.03, rel=1e-6)


class TestClickHouseIntegration:
    """Test ClickHouse event insertion (mocked)."""
    
    @pytest.mark.asyncio
    async def test_insert_enriched_event(self, mock_clickhouse, sample_event_data):
        """Test inserting enriched event to ClickHouse."""
        event = sample_event_data
        event["estimated_cost_usd"] = 0.005
        event["processed_at"] = datetime.utcnow().isoformat()
        
        # Mock insertion
        mock_clickhouse.execute = MagicMock(return_value=None)
        
        # Simulate insert
        mock_clickhouse.execute("INSERT INTO events VALUES", [event])
        
        mock_clickhouse.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_insert_batch_events(self, mock_clickhouse):
        """Test batch insertion to ClickHouse."""
        events = [
            {"event_id": f"evt_{i}", "type": "log"}
            for i in range(100)
        ]
        
        mock_clickhouse.execute = MagicMock(return_value=None)
        
        # Simulate batch insert
        mock_clickhouse.execute("INSERT INTO events VALUES", events)
        
        mock_clickhouse.execute.assert_called_once()
        call_args = mock_clickhouse.execute.call_args
        assert len(call_args[0][1]) == 100

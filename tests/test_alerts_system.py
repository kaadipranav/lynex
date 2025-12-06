"""
Unit tests for alerts system.
Verifies correct project_id usage and alert evaluation logic.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add processor to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "processor"))

from alerts import (
    AlertCondition,
    AlertSeverity,
    AlertRule,
    Alert,
    evaluate_rule,
    evaluate_event,
    get_nested_value,
    RuleManager,
)


@pytest.mark.unit
class TestProjectIdMatching:
    """Test that alerts correctly match project_id (not projectId)."""
    
    def test_alert_matches_correct_project_id(self):
        """Test that alert matches event with same project_id."""
        rule = AlertRule(
            id="rule_1",
            name="Test Rule",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.WARNING,
            event_type="error",
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",  # Matches rule
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        # Should trigger alert
        assert alert is not None
        assert alert.project_id == "proj_123"
    
    def test_alert_ignores_different_project_id(self):
        """Test that alert does NOT match event with different project_id."""
        rule = AlertRule(
            id="rule_1",
            name="Test Rule",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.WARNING,
            event_type="error",
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_456",  # Different project
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        # Should NOT trigger alert
        assert alert is None
    
    def test_alert_uses_snake_case_project_id(self):
        """Test that alert system uses project_id (snake_case), not projectId (camelCase)."""
        rule = AlertRule(
            id="rule_1",
            name="Test Rule",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.WARNING,
            event_type="error",
        )
        
        # Event with snake_case project_id (correct)
        event_snake = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event_snake, enriched)
        assert alert is not None  # Should match
        
        # Event with camelCase projectId (should NOT match)
        event_camel = {
            "event_id": "evt_2",
            "projectId": "proj_123",  # Wrong case
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        alert_camel = evaluate_rule(rule, event_camel, enriched)
        assert alert_camel is None  # Should NOT match


@pytest.mark.unit
class TestAlertConditions:
    """Test different alert condition types."""
    
    def test_error_count_condition(self):
        """Test ERROR_COUNT condition triggers on error events."""
        rule = AlertRule(
            id="rule_1",
            name="Error Alert",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.CRITICAL,
            event_type="error",
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "error",
            "body": {"message": "Database connection failed"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert "Database connection failed" in alert.message
    
    def test_latency_threshold_condition(self):
        """Test LATENCY_THRESHOLD condition triggers on high latency."""
        rule = AlertRule(
            id="rule_2",
            name="High Latency",
            project_id="proj_123",
            condition=AlertCondition.LATENCY_THRESHOLD,
            threshold=1000,  # 1 second
            severity=AlertSeverity.WARNING,
            field_path="body.latencyMs",
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "model_response",
            "body": {"latencyMs": 1500},  # Over threshold
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        assert alert is not None
        assert "1500ms" in alert.message
        assert "1000ms" in alert.message  # Shows threshold
    
    def test_cost_threshold_condition(self):
        """Test COST_THRESHOLD condition triggers on high cost."""
        rule = AlertRule(
            id="rule_3",
            name="High Cost",
            project_id="proj_123",
            condition=AlertCondition.COST_THRESHOLD,
            threshold=0.10,  # $0.10
            severity=AlertSeverity.WARNING,
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "token_usage",
            "body": {"model": "gpt-4"},
        }
        
        enriched = {
            "estimated_cost_usd": 0.15  # Over threshold
        }
        
        alert = evaluate_rule(rule, event, enriched)
        
        assert alert is not None
        assert "$0.15" in alert.message or "0.15" in alert.message
    
    def test_event_match_condition(self):
        """Test EVENT_MATCH condition with field matching."""
        rule = AlertRule(
            id="rule_4",
            name="GPT-4 Usage",
            project_id="proj_123",
            condition=AlertCondition.EVENT_MATCH,
            threshold=0,
            severity=AlertSeverity.INFO,
            field_path="body.model",
            field_value="gpt-4",
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "token_usage",
            "body": {"model": "gpt-4"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        assert alert is not None
        assert "gpt-4" in alert.message


@pytest.mark.unit
class TestNestedValueExtraction:
    """Test nested value extraction from events."""
    
    def test_get_simple_value(self):
        """Test extracting simple top-level value."""
        obj = {"name": "test", "value": 123}
        
        result = get_nested_value(obj, "name")
        assert result == "test"
    
    def test_get_nested_value(self):
        """Test extracting nested value with dot notation."""
        obj = {
            "body": {
                "model": "gpt-4",
                "latencyMs": 150
            }
        }
        
        result = get_nested_value(obj, "body.model")
        assert result == "gpt-4"
        
        result = get_nested_value(obj, "body.latencyMs")
        assert result == 150
    
    def test_get_deeply_nested_value(self):
        """Test extracting deeply nested value."""
        obj = {
            "context": {
                "user": {
                    "metadata": {
                        "tier": "PRO"
                    }
                }
            }
        }
        
        result = get_nested_value(obj, "context.user.metadata.tier")
        assert result == "PRO"
    
    def test_get_nonexistent_value_returns_none(self):
        """Test that nonexistent path returns None."""
        obj = {"name": "test"}
        
        result = get_nested_value(obj, "nonexistent.path")
        assert result is None
    
    def test_get_value_from_non_dict_returns_none(self):
        """Test that accessing non-dict returns None."""
        obj = {"value": 123}
        
        result = get_nested_value(obj, "value.nested")
        assert result is None


@pytest.mark.unit
class TestAlertEvaluation:
    """Test alert evaluation for multiple rules."""
    
    def test_evaluate_multiple_rules(self):
        """Test evaluating event against multiple rules."""
        rules = [
            AlertRule(
                id="rule_1",
                name="Error Alert",
                project_id="proj_123",
                condition=AlertCondition.ERROR_COUNT,
                threshold=1,
                severity=AlertSeverity.CRITICAL,
                event_type="error",
            ),
            AlertRule(
                id="rule_2",
                name="All Events",
                project_id="proj_123",
                condition=AlertCondition.EVENT_MATCH,
                threshold=0,
                severity=AlertSeverity.INFO,
                field_path="type",
                field_value="error",
            ),
        ]
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        # Manually evaluate (since evaluate_event uses rule_manager)
        alerts = []
        for rule in rules:
            alert = evaluate_rule(rule, event, enriched)
            if alert:
                alerts.append(alert)
        
        # Both rules should trigger
        assert len(alerts) == 2
        assert alerts[0].rule_id == "rule_1"
        assert alerts[1].rule_id == "rule_2"
    
    def test_disabled_rule_not_evaluated(self):
        """Test that disabled rules are not evaluated."""
        rule = AlertRule(
            id="rule_1",
            name="Disabled Rule",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.WARNING,
            event_type="error",
            enabled=False,  # Disabled
        )
        
        event = {
            "event_id": "evt_1",
            "project_id": "proj_123",
            "type": "error",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        # Should NOT trigger (disabled)
        assert alert is None


@pytest.mark.unit
class TestRuleManager:
    """Test rule manager for loading rules from database."""
    
    @pytest.mark.asyncio
    async def test_load_rules_from_database(self):
        """Test loading rules from MongoDB."""
        mock_db = MagicMock()
        
        # Mock cursor with async iteration
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = AsyncMock(return_value=iter([
            {
                "_id": "rule_1",
                "name": "Test Rule",
                "project_id": "proj_123",
                "condition": "error_count",
                "threshold": 10,
                "severity": "warning",
                "enabled": True,
            }
        ]))
        
        mock_db.alert_rules.find = MagicMock(return_value=mock_cursor)
        
        manager = RuleManager()
        
        with patch("alerts.db", mock_db):
            await manager.load_rules()
            
            rules = manager.get_rules()
            assert len(rules) == 1
            assert rules[0].name == "Test Rule"
            assert rules[0].project_id == "proj_123"
    
    @pytest.mark.asyncio
    async def test_load_rules_skips_invalid(self):
        """Test that invalid rules are skipped during load."""
        mock_db = MagicMock()
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = AsyncMock(return_value=iter([
            {
                "_id": "rule_1",
                "name": "Valid Rule",
                "project_id": "proj_123",
                "condition": "error_count",
                "threshold": 10,
                "severity": "warning",
                "enabled": True,
            },
            {
                "_id": "rule_2",
                # Missing required fields - invalid
                "name": "Invalid Rule",
            }
        ]))
        
        mock_db.alert_rules.find = MagicMock(return_value=mock_cursor)
        
        manager = RuleManager()
        
        with patch("alerts.db", mock_db):
            await manager.load_rules()
            
            rules = manager.get_rules()
            # Should only load the valid rule
            assert len(rules) == 1
            assert rules[0].name == "Valid Rule"


@pytest.mark.unit
class TestAlertMetadata:
    """Test alert metadata and context."""
    
    def test_alert_includes_event_metadata(self):
        """Test that triggered alert includes event metadata."""
        rule = AlertRule(
            id="rule_1",
            name="Error Alert",
            project_id="proj_123",
            condition=AlertCondition.ERROR_COUNT,
            threshold=1,
            severity=AlertSeverity.CRITICAL,
            event_type="error",
        )
        
        event = {
            "event_id": "evt_123",
            "project_id": "proj_123",
            "type": "error",
            "timestamp": "2025-12-06T10:00:00Z",
            "body": {"message": "Test error"},
        }
        
        enriched = {}
        
        alert = evaluate_rule(rule, event, enriched)
        
        assert alert is not None
        assert alert.event_id == "evt_123"
        assert alert.metadata is not None
        assert alert.metadata["event_type"] == "error"
        assert alert.metadata["timestamp"] == "2025-12-06T10:00:00Z"

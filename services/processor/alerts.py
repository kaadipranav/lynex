"""
Alert Rule Engine for WatchLLM.
Evaluates events against configured alert rules.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("watchllm.alerts")


class AlertCondition(Enum):
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    COST_THRESHOLD = "cost_threshold"
    LATENCY_THRESHOLD = "latency_threshold"
    ERROR_COUNT = "error_count"
    EVENT_MATCH = "event_match"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Definition of an alert rule."""
    id: str
    name: str
    project_id: str
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    
    # For event_match condition
    event_type: Optional[str] = None
    field_path: Optional[str] = None  # e.g., "body.level" or "body.model"
    field_value: Optional[str] = None


@dataclass
class Alert:
    """A triggered alert."""
    rule_id: str
    rule_name: str
    project_id: str
    severity: AlertSeverity
    message: str
    event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


from datetime import datetime
from shared.database import db

# ... (imports)

# ... (AlertRule and Alert classes)

class RuleManager:
    def __init__(self):
        self.rules: List[AlertRule] = []
        
    async def load_rules(self):
        """Load rules from MongoDB."""
        try:
            # Use the shared db instance
            cursor = db.alert_rules.find({"enabled": True})
            rules = []
            async for doc in cursor:
                try:
                    rules.append(AlertRule(
                        id=str(doc["_id"]),
                        name=doc["name"],
                        project_id=doc["project_id"],
                        condition=AlertCondition(doc["condition"]),
                        threshold=doc["threshold"],
                        severity=AlertSeverity(doc["severity"]),
                        enabled=doc["enabled"],
                        event_type=doc.get("event_type"),
                        field_path=doc.get("field_path"),
                        field_value=doc.get("field_value"),
                    ))
                except Exception as e:
                    logger.error(f"Skipping invalid rule {doc.get('_id')}: {e}")
            
            self.rules = rules
            logger.info(f"Loaded {len(rules)} alert rules")
        except Exception as e:
            logger.error(f"Failed to load alert rules: {e}")

    def get_rules(self) -> List[AlertRule]:
        return self.rules

rule_manager = RuleManager()

# Default demo rules (fallback if DB is empty)
DEMO_RULES = [
    AlertRule(
        id="rule_1",
        name="High Error Rate",
        project_id="proj_demo",
        condition=AlertCondition.ERROR_COUNT,
        threshold=1,
        severity=AlertSeverity.WARNING,
        event_type="error",
    ),
    # ... other demo rules
]

def get_nested_value(obj: Dict, path: str) -> Any:
    """Get a nested value from a dict using dot notation."""
    keys = path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def evaluate_rule(rule: AlertRule, event: Dict[str, Any], enriched: Dict[str, Any]) -> Optional[Alert]:
    """Evaluate a single rule against an event."""
    
    if not rule.enabled:
        return None
    
    if rule.project_id != event.get("project_id"):
        return None
    
    # Check event type filter
    if rule.event_type and event.get("type") != rule.event_type:
        return None
    
    triggered = False
    message = ""
    
    if rule.condition == AlertCondition.ERROR_COUNT:
        if event.get("type") == "error":
            triggered = True
            error_msg = event.get("body", {}).get("message", "Unknown error")
            message = f"Error occurred: {error_msg}"
    
    elif rule.condition == AlertCondition.LATENCY_THRESHOLD:
        if rule.field_path:
            latency = get_nested_value(event, rule.field_path)
            if latency and latency > rule.threshold:
                triggered = True
                message = f"High latency detected: {latency}ms (threshold: {rule.threshold}ms)"
    
    elif rule.condition == AlertCondition.COST_THRESHOLD:
        cost = enriched.get("estimated_cost_usd", 0)
        if cost > rule.threshold:
            triggered = True
            message = f"High cost event: ${cost:.4f} (threshold: ${rule.threshold})"
    
    elif rule.condition == AlertCondition.EVENT_MATCH:
        if rule.field_path and rule.field_value:
            value = get_nested_value(event, rule.field_path)
            if str(value) == str(rule.field_value):
                triggered = True
                message = f"Event matched: {rule.field_path} = {rule.field_value}"
    
    if triggered:
        return Alert(
            rule_id=rule.id,
            rule_name=rule.name,
            project_id=rule.project_id,
            severity=rule.severity,
            message=message,
            event_id=event.get("event_id"),
            metadata={
                "event_type": event.get("type"),
                "timestamp": event.get("timestamp"),
            }
        )
    
    return None


def evaluate_event(event: Dict[str, Any], enriched: Dict[str, Any]) -> List[Alert]:
    """Evaluate all rules against an event and return triggered alerts."""
    alerts = []
    
    # Use loaded rules, fallback to demo if empty (optional)
    rules = rule_manager.get_rules()
    if not rules and not db.client: # If DB not connected or empty, maybe use demo?
         # For now, just use what we have.
         pass

    for rule in rules:
        try:
            alert = evaluate_rule(rule, event, enriched)
            if alert:
                alerts.append(alert)
                logger.info(f"🚨 Alert triggered: {alert.rule_name} - {alert.message}")
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
    
    return alerts

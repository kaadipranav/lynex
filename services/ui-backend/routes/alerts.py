"""
Alert Rules Management Routes.
CRUD operations for alert rules.
"""

import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).resolve().parent.parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from auth.supabase_middleware import require_user, User
from shared.database import get_db
from bson import ObjectId

router = APIRouter()


# =============================================================================
# Models
# =============================================================================

class AlertCondition(str, Enum):
    ERROR_RATE_THRESHOLD = "error_rate_threshold"
    COST_THRESHOLD = "cost_threshold"
    LATENCY_THRESHOLD = "latency_threshold"
    ERROR_COUNT = "error_count"
    EVENT_MATCH = "event_match"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    project_id: str
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    event_type: Optional[str] = None
    field_path: Optional[str] = None
    field_value: Optional[str] = None


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    condition: Optional[AlertCondition] = None
    threshold: Optional[float] = None
    severity: Optional[AlertSeverity] = None
    enabled: Optional[bool] = None
    event_type: Optional[str] = None
    field_path: Optional[str] = None
    field_value: Optional[str] = None


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    project_id: str
    condition: AlertCondition
    threshold: float
    severity: AlertSeverity
    enabled: bool
    event_type: Optional[str] = None
    field_path: Optional[str] = None
    field_value: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/alerts/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    project_id: str,
    user: User = Depends(require_user),
):
    """List all alert rules for a project."""
    db = await get_db()
    
    cursor = db.alert_rules.find({"project_id": project_id})
    rules = []
    
    async for doc in cursor:
        rules.append(AlertRuleResponse(
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
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow()),
        ))
    
    return rules


@router.post("/alerts/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    rule: AlertRuleCreate,
    user: User = Depends(require_user),
):
    """Create a new alert rule."""
    db = await get_db()
    
    now = datetime.utcnow()
    doc = {
        "name": rule.name,
        "project_id": rule.project_id,
        "condition": rule.condition.value,
        "threshold": rule.threshold,
        "severity": rule.severity.value,
        "enabled": rule.enabled,
        "event_type": rule.event_type,
        "field_path": rule.field_path,
        "field_value": rule.field_value,
        "created_at": now,
        "updated_at": now,
    }
    
    result = await db.alert_rules.insert_one(doc)
    
    return AlertRuleResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in doc.items() if k != "_id"},
        condition=rule.condition,
        severity=rule.severity,
    )


@router.get("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    user: User = Depends(require_user),
):
    """Get a specific alert rule."""
    db = await get_db()
    
    try:
        doc = await db.alert_rules.find_one({"_id": ObjectId(rule_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID")
    
    if not doc:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    return AlertRuleResponse(
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
        created_at=doc.get("created_at", datetime.utcnow()),
        updated_at=doc.get("updated_at", datetime.utcnow()),
    )


@router.patch("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    updates: AlertRuleUpdate,
    user: User = Depends(require_user),
):
    """Update an alert rule."""
    db = await get_db()
    
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Convert enums to strings
    if "condition" in update_data:
        update_data["condition"] = update_data["condition"].value
    if "severity" in update_data:
        update_data["severity"] = update_data["severity"].value
    
    try:
        result = await db.alert_rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": update_data}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    # Fetch updated doc
    doc = await db.alert_rules.find_one({"_id": ObjectId(rule_id)})
    
    return AlertRuleResponse(
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
        created_at=doc.get("created_at", datetime.utcnow()),
        updated_at=doc.get("updated_at", datetime.utcnow()),
    )


@router.delete("/alerts/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    user: User = Depends(require_user),
):
    """Delete an alert rule."""
    db = await get_db()
    
    try:
        result = await db.alert_rules.delete_one({"_id": ObjectId(rule_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    return None

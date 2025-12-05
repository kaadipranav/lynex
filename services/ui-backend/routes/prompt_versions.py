"""
Prompt Version Management API.
Track, version, and diff prompt templates.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
import logging
import uuid
import difflib

from auth.supabase_middleware import require_user, User
from shared.database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.prompt_version import (
    PromptVersion,
    PromptVersionCreate,
    PromptVersionResponse,
    PromptDiff,
)

logger = logging.getLogger("watchllm.ui_backend.prompt_versions")

router = APIRouter()

# =============================================================================
# Helper Functions
# =============================================================================

def compute_diff(version_a: dict, version_b: dict) -> PromptDiff:
    """
    Compute differences between two prompt versions.
    Uses difflib for line-by-line comparison.
    """
    # Split templates into lines
    lines_a = version_a["template"].splitlines()
    lines_b = version_b["template"].splitlines()
    
    # Compute diff
    diff = difflib.unified_diff(lines_a, lines_b, lineterm='')
    
    added_lines = []
    removed_lines = []
    unchanged_lines = []
    
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])
        elif line.startswith('-') and not line.startswith('---'):
            removed_lines.append(line[1:])
        elif not line.startswith('@@'):
            unchanged_lines.append(line)
    
    # Check metadata changes
    model_changed = version_a.get("model") != version_b.get("model")
    temp_changed = version_a.get("temperature") != version_b.get("temperature")
    
    vars_a = set(version_a.get("variables", {}).keys())
    vars_b = set(version_b.get("variables", {}).keys())
    variables_changed = list(vars_a.symmetric_difference(vars_b))
    
    # Performance deltas
    cost_delta = None
    latency_delta = None
    success_delta = None
    
    if version_a.get("avg_cost") and version_b.get("avg_cost"):
        cost_delta = version_b["avg_cost"] - version_a["avg_cost"]
    
    if version_a.get("avg_latency_ms") and version_b.get("avg_latency_ms"):
        latency_delta = version_b["avg_latency_ms"] - version_a["avg_latency_ms"]
    
    if version_a.get("success_rate") and version_b.get("success_rate"):
        success_delta = version_b["success_rate"] - version_a["success_rate"]
    
    return PromptDiff(
        version_a_id=version_a["version_id"],
        version_b_id=version_b["version_id"],
        version_a_number=version_a["version_number"],
        version_b_number=version_b["version_number"],
        added_lines=added_lines,
        removed_lines=removed_lines,
        unchanged_lines=unchanged_lines,
        model_changed=model_changed,
        temperature_changed=temp_changed,
        variables_changed=variables_changed,
        cost_delta=cost_delta,
        latency_delta=latency_delta,
        success_rate_delta=success_delta,
    )


async def get_latest_version_number(db: AsyncIOMotorDatabase, project_id: str, prompt_name: str) -> int:
    """Get the latest version number for a prompt."""
    latest = await db["prompt_versions"].find_one(
        {"project_id": project_id, "prompt_name": prompt_name},
        sort=[("version_number", -1)]
    )
    return latest["version_number"] if latest else 0


# =============================================================================
# Routes
# =============================================================================

@router.get("/prompts", response_model=List[dict])
async def list_prompts(
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all unique prompts (grouped by name) for the project.
    Returns latest version of each prompt.
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        
        # Aggregate to get latest version of each prompt
        pipeline = [
            {"$match": {"project_id": project_id}},
            {"$sort": {"version_number": -1}},
            {"$group": {
                "_id": "$prompt_name",
                "latest_version": {"$first": "$$ROOT"}
            }}
        ]
        
        result = await db["prompt_versions"].aggregate(pipeline).to_list(length=100)
        
        prompts = []
        for item in result:
            version = item["latest_version"]
            version.pop("_id", None)
            prompts.append({
                "prompt_name": item["_id"],
                "latest_version": version,
                "version_count": await db["prompt_versions"].count_documents({
                    "project_id": project_id,
                    "prompt_name": item["_id"]
                })
            })
        
        return prompts
    
    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prompts"
        )


@router.get("/prompts/{prompt_name}/versions", response_model=List[PromptVersionResponse])
async def list_prompt_versions(
    prompt_name: str,
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all versions of a specific prompt.
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        
        versions = await db["prompt_versions"].find({
            "project_id": project_id,
            "prompt_name": prompt_name
        }).sort("version_number", -1).to_list(length=100)
        
        for v in versions:
            v.pop("_id", None)
        
        return versions
    
    except Exception as e:
        logger.error(f"Failed to list prompt versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prompt versions"
        )


@router.post("/prompts", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_version(
    prompt_data: PromptVersionCreate,
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new version of a prompt template.
    Automatically increments version number.
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        user_id = user.id
        
        # Get next version number
        version_number = await get_latest_version_number(db, project_id, prompt_data.prompt_name) + 1
        
        version_id = f"pv_{uuid.uuid4().hex[:12]}"
        
        version = {
            "version_id": version_id,
            "project_id": project_id,
            "prompt_name": prompt_data.prompt_name,
            "version_number": version_number,
            "template": prompt_data.template,
            "variables": prompt_data.variables,
            "metadata": prompt_data.metadata,
            "model": prompt_data.model,
            "temperature": prompt_data.temperature,
            "max_tokens": prompt_data.max_tokens,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "usage_count": 0,
            "avg_cost": None,
            "avg_latency_ms": None,
            "success_rate": None,
        }
        
        await db["prompt_versions"].insert_one(version)
        
        logger.info(f"Created prompt version {version_id} ({prompt_data.prompt_name} v{version_number})")
        
        version.pop("_id", None)
        return version
    
    except Exception as e:
        logger.error(f"Failed to create prompt version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt version"
        )


@router.get("/prompts/{prompt_name}/versions/{version_number}", response_model=PromptVersionResponse)
async def get_prompt_version(
    prompt_name: str,
    version_number: int,
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a specific version of a prompt.
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        
        version = await db["prompt_versions"].find_one({
            "project_id": project_id,
            "prompt_name": prompt_name,
            "version_number": version_number
        })
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt version not found"
            )
        
        version.pop("_id", None)
        return version
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch prompt version"
        )


@router.get("/prompts/{prompt_name}/diff", response_model=PromptDiff)
async def diff_prompt_versions(
    prompt_name: str,
    version_a: int,
    version_b: int,
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Compare two versions of a prompt and return the diff.
    
    Query params:
    - version_a: First version number to compare
    - version_b: Second version number to compare
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        
        # Fetch both versions
        ver_a = await db["prompt_versions"].find_one({
            "project_id": project_id,
            "prompt_name": prompt_name,
            "version_number": version_a
        })
        
        ver_b = await db["prompt_versions"].find_one({
            "project_id": project_id,
            "prompt_name": prompt_name,
            "version_number": version_b
        })
        
        if not ver_a or not ver_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both versions not found"
            )
        
        # Compute diff
        diff = compute_diff(ver_a, ver_b)
        
        return diff
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compute diff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute diff"
        )


@router.delete("/prompts/{prompt_name}/versions/{version_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_version(
    prompt_name: str,
    version_number: int,
    user: User = Depends(require_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a specific prompt version.
    """
    try:
        project_id = user.user_metadata.get("project_id", user.id)
        
        result = await db["prompt_versions"].delete_one({
            "project_id": project_id,
            "prompt_name": prompt_name,
            "version_number": version_number
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt version not found"
            )
        
        logger.info(f"Deleted prompt version {prompt_name} v{version_number}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt version"
        )

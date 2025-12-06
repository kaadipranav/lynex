"""
Statistics and aggregation routes.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from schemas import (
    OverviewStats,
    TokenUsageByModel,
    EventCountByType,
    TimeSeriesResponse,
    TimeSeriesPoint,
    ErrorResponse,
)
import clickhouse as ch
from auth.supabase_middleware import require_user, User

logger = logging.getLogger("watchllm.query.stats")
router = APIRouter()


@router.get(
    "/stats/overview",
    response_model=OverviewStats,
)
async def get_overview_stats(
    project_id: str = Query(..., description="Project ID"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    user: User = Depends(require_user),
):
    """
    Get overview statistics for the dashboard.
    
    Returns:
    - Total events
    - Error count and rate
    - Total cost
    - Token usage
    - Avg latency
    """
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    sql = """
    SELECT
        count() as total_events,
        countIf(type = 'error') as total_errors,
        sum(estimated_cost_usd) as total_cost_usd,
        sumIf(JSONExtractInt(body, 'inputTokens'), type = 'token_usage') +
        sumIf(JSONExtractInt(body, 'outputTokens'), type = 'token_usage') as total_tokens,
        avgIf(JSONExtractInt(body, 'latencyMs'), type = 'model_response') as avg_latency_ms
    FROM events
    WHERE project_id = %(project_id)s
      AND timestamp >= %(start_time)s
    """
    
    params = {
        "project_id": project_id,
        "start_time": start_time
    }
    
    try:
        client = await ch.get_client()
        result = await client.query(sql, params)
        
        if not result:
            return OverviewStats(
                total_events=0,
                total_errors=0,
                error_rate_pct=0,
                total_cost_usd=0,
                total_tokens=0,
            )
        
        row = result[0]
        total_events = row["total_events"]
        total_errors = row["total_errors"]
        
        error_rate = (total_errors / total_events * 100) if total_events > 0 else 0
        
        return OverviewStats(
            total_events=total_events,
            total_errors=total_errors,
            error_rate_pct=round(error_rate, 2),
            total_cost_usd=round(row.get("total_cost_usd", 0), 4),
            total_tokens=row.get("total_tokens", 0),
            avg_latency_ms=round(row.get("avg_latency_ms", 0), 2) if row.get("avg_latency_ms") else None,
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )


@router.get(
    "/stats/tokens",
    response_model=List[TokenUsageByModel],
)
async def get_token_usage_by_model(
    project_id: str = Query(..., description="Project ID"),
    hours: int = Query(24, ge=1, le=720),
    user: User = Depends(require_user),
):
    """Get token usage grouped by model."""
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    sql = """
    SELECT
        JSONExtractString(body, 'model') as model,
        sum(JSONExtractInt(body, 'inputTokens')) as input_tokens,
        sum(JSONExtractInt(body, 'outputTokens')) as output_tokens,
        sum(estimated_cost_usd) as total_cost_usd,
        count() as request_count
    FROM events
    WHERE project_id = %(project_id)s
      AND type = 'token_usage'
      AND timestamp >= %(start_time)s
    GROUP BY model
    ORDER BY total_cost_usd DESC
    """
    
    params = {
        "project_id": project_id,
        "start_time": start_time
    }
    
    try:
        client = await ch.get_client()
        result = await client.query(sql, params)
        
        return [
            TokenUsageByModel(
                model=row["model"],
                input_tokens=row["input_tokens"],
                output_tokens=row["output_tokens"],
                total_cost_usd=round(row["total_cost_usd"], 6),
                request_count=row["request_count"],
            )
            for row in result
        ]
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )


@router.get(
    "/stats/events-by-type",
    response_model=List[EventCountByType],
)
async def get_events_by_type(
    project_id: str = Query(..., description="Project ID"),
    hours: int = Query(24, ge=1, le=720),
    user: User = Depends(require_user),
):
    """Get event count grouped by type."""
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    sql = """
    SELECT
        type,
        count() as count
    FROM events
    WHERE project_id = %(project_id)s
      AND timestamp >= %(start_time)s
    GROUP BY type
    ORDER BY count DESC
    """
    
    params = {
        "project_id": project_id,
        "start_time": start_time
    }
    
    try:
        client = await ch.get_client()
        result = await client.query(sql, params)
        
        return [
            EventCountByType(type=row["type"], count=row["count"])
            for row in result
        ]
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )


@router.get(
    "/stats/timeseries",
    response_model=TimeSeriesResponse,
)
async def get_timeseries(
    project_id: str = Query(..., description="Project ID"),
    metric: str = Query(..., description="Metric: requests, errors, tokens, cost"),
    hours: int = Query(24, ge=1, le=720),
    interval: str = Query("1h", description="Time interval: 1m, 5m, 1h, 1d"),
    user: User = Depends(require_user),
):
    """Get time series data for charting."""
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Map interval to ClickHouse function
    interval_map = {
        "1m": "toStartOfMinute",
        "5m": "toStartOfFiveMinutes",
        "1h": "toStartOfHour",
        "1d": "toStartOfDay",
    }
    
    # Validate interval is in whitelist
    if interval not in interval_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid interval: {interval}. Must be one of: {', '.join(interval_map.keys())}"}
        )
    
    time_func = interval_map[interval]
    
    # Map metric to SQL value expression (whitelisted values only)
    metric_map = {
        "requests": "count()",
        "errors": "countIf(type = 'error')",
        "tokens": "sum(JSONExtractInt(body, 'inputTokens') + JSONExtractInt(body, 'outputTokens'))",
        "cost": "sum(estimated_cost_usd)",
    }
    
    if metric not in metric_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Unknown metric: {metric}. Must be one of: {', '.join(metric_map.keys())}"}
        )
    
    value_sql = metric_map[metric]
    
    # Safe to use f-string here since time_func and value_sql are from whitelisted maps
    sql = f"""
    SELECT
        {time_func}(timestamp) as bucket,
        {value_sql} as value
    FROM events
    WHERE project_id = %(project_id)s
      AND timestamp >= %(start_time)s
    GROUP BY bucket
    ORDER BY bucket
    """
    
    params = {
        "project_id": project_id,
        "start_time": start_time
    }
    
    try:
        client = await ch.get_client()
        result = await client.query(sql, params)
        
        data = [
            TimeSeriesPoint(
                timestamp=row["bucket"] if isinstance(row["bucket"], datetime) else datetime.fromisoformat(row["bucket"]),
                value=float(row["value"]),
            )
            for row in result
        ]
        
        return TimeSeriesResponse(metric=metric, data=data)
        
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database unavailable"}
        )

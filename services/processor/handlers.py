"""
Event Processing Handlers.
This is where the actual event processing logic lives.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("sentryai.processor.handlers")


# =============================================================================
# Main Event Processor
# =============================================================================

async def process_event(event: Dict[str, Any]):
    """
    Process a single event.
    
    This function:
    1. Enriches the event with additional metadata
    2. Computes derived fields (cost estimates, etc.)
    3. Stores the event in ClickHouse (Task 7)
    4. Checks alert rules (Task 14)
    """
    event_type = event.get("type")
    event_id = event.get("event_id")
    project_id = event.get("project_id")
    
    logger.debug(f"Processing {event_type} event: {event_id}")
    
    # Enrich the event
    enriched = await enrich_event(event)
    
    # Route to type-specific handler
    handler = EVENT_HANDLERS.get(event_type, handle_unknown)
    await handler(enriched)
    
    # TODO: Task 7 - Write to ClickHouse
    # await clickhouse.insert_event(enriched)
    
    # TODO: Task 14 - Check alert rules
    # await alerts.check_rules(enriched)
    
    logger.debug(f"Event {event_id} processed successfully")


# =============================================================================
# Event Enrichment
# =============================================================================

async def enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich event with additional metadata.
    """
    enriched = event.copy()
    
    # Add processing timestamp
    enriched["processed_at"] = datetime.utcnow().isoformat()
    
    # Calculate latency from queue
    if event.get("queued_at"):
        try:
            queued = datetime.fromisoformat(event["queued_at"])
            latency_ms = (datetime.utcnow() - queued).total_seconds() * 1000
            enriched["queue_latency_ms"] = round(latency_ms, 2)
        except:
            pass
    
    # Enrich token_usage events with cost estimates
    if event.get("type") == "token_usage":
        enriched = await enrich_token_usage(enriched)
    
    return enriched


async def enrich_token_usage(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich token usage events with cost estimates.
    """
    body = event.get("body", {})
    model = body.get("model", "").lower()
    input_tokens = body.get("inputTokens", 0)
    output_tokens = body.get("outputTokens", 0)
    
    # Cost per 1K tokens (approximate, as of late 2024)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    # Find matching pricing
    pricing = None
    for model_key, price in PRICING.items():
        if model_key in model:
            pricing = price
            break
    
    if pricing:
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        event["estimated_cost_usd"] = round(total_cost, 6)
        event["cost_breakdown"] = {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "model": model,
        }
        
        logger.debug(f"Estimated cost for {model}: ${total_cost:.6f}")
    
    return event


# =============================================================================
# Type-Specific Handlers
# =============================================================================

async def handle_log(event: Dict[str, Any]):
    """Handle log events."""
    body = event.get("body", {})
    level = body.get("level", "info")
    message = body.get("message", "")
    
    # Log at appropriate level
    if level == "error":
        logger.warning(f"[{event['project_id']}] ERROR: {message[:100]}")
    elif level == "warn":
        logger.info(f"[{event['project_id']}] WARN: {message[:100]}")
    else:
        logger.debug(f"[{event['project_id']}] {level.upper()}: {message[:50]}")


async def handle_error(event: Dict[str, Any]):
    """Handle error events."""
    body = event.get("body", {})
    message = body.get("message", "Unknown error")
    stack = body.get("stack", "")
    
    logger.warning(f"[{event['project_id']}] Error captured: {message[:100]}")
    
    # TODO: Group errors by fingerprint
    # TODO: Check if this triggers an alert


async def handle_token_usage(event: Dict[str, Any]):
    """Handle token usage events."""
    body = event.get("body", {})
    model = body.get("model", "unknown")
    input_tokens = body.get("inputTokens", 0)
    output_tokens = body.get("outputTokens", 0)
    
    logger.info(
        f"[{event['project_id']}] Token usage: {model} - "
        f"in:{input_tokens} out:{output_tokens}"
    )
    
    if event.get("estimated_cost_usd"):
        logger.info(f"   Estimated cost: ${event['estimated_cost_usd']:.6f}")


async def handle_model_response(event: Dict[str, Any]):
    """Handle model response events."""
    body = event.get("body", {})
    model = body.get("model", "unknown")
    latency = body.get("latencyMs", 0)
    
    logger.info(
        f"[{event['project_id']}] Model call: {model} - {latency}ms"
    )


async def handle_span(event: Dict[str, Any]):
    """Handle span/trace events."""
    body = event.get("body", {})
    name = body.get("name", "unknown")
    
    logger.debug(f"[{event['project_id']}] Span: {name}")


async def handle_tool_call(event: Dict[str, Any]):
    """Handle tool call events."""
    body = event.get("body", {})
    tool_name = body.get("toolName", "unknown")
    latency = body.get("latencyMs", 0)
    
    logger.info(f"[{event['project_id']}] Tool call: {tool_name} - {latency}ms")


async def handle_agent_action(event: Dict[str, Any]):
    """Handle agent action events."""
    body = event.get("body", {})
    action = body.get("action", "unknown")
    agent = body.get("agentName", "default")
    
    logger.info(f"[{event['project_id']}] Agent '{agent}': {action}")


async def handle_retrieval(event: Dict[str, Any]):
    """Handle RAG retrieval events."""
    body = event.get("body", {})
    query = body.get("query", "")[:50]
    results_count = len(body.get("results", []))
    
    logger.info(f"[{event['project_id']}] Retrieval: '{query}...' - {results_count} results")


async def handle_eval_metric(event: Dict[str, Any]):
    """Handle eval metric events."""
    body = event.get("body", {})
    metric = body.get("metric", "unknown")
    value = body.get("value", 0)
    
    logger.info(f"[{event['project_id']}] Eval: {metric} = {value}")


async def handle_unknown(event: Dict[str, Any]):
    """Handle unknown event types."""
    logger.debug(f"[{event['project_id']}] Unknown event type: {event.get('type')}")


# =============================================================================
# Handler Registry
# =============================================================================

EVENT_HANDLERS = {
    "log": handle_log,
    "error": handle_error,
    "token_usage": handle_token_usage,
    "model_response": handle_model_response,
    "span": handle_span,
    "tool_call": handle_tool_call,
    "agent_action": handle_agent_action,
    "retrieval": handle_retrieval,
    "eval_metric": handle_eval_metric,
    "message": handle_log,  # Messages use same handler as logs
    "custom": handle_unknown,
}

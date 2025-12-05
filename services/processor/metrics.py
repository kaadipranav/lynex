"""
Prometheus Metrics Exporter
Exposes /metrics endpoint for monitoring and alerting.
Required for enterprise deployments.
"""

import time
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)

# Create a custom registry to avoid conflicts
REGISTRY = CollectorRegistry()

# =============================================================================
# Application Info
# =============================================================================

app_info = Info(
    "lynex_app",
    "Lynex application information",
    registry=REGISTRY,
)
app_info.info({
    "version": "1.0.0",
    "service": "processor",
    "environment": "production",
})

# =============================================================================
# Event Metrics
# =============================================================================

# Total events processed
events_processed_total = Counter(
    "lynex_events_processed_total",
    "Total number of events processed",
    ["project_id", "event_type", "status"],
    registry=REGISTRY,
)

# Event processing duration
event_processing_duration = Histogram(
    "lynex_event_processing_duration_seconds",
    "Time spent processing events",
    ["event_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

# Event queue depth
event_queue_depth = Gauge(
    "lynex_event_queue_depth",
    "Number of events waiting in queue",
    registry=REGISTRY,
)

# Event queue latency
event_queue_latency = Histogram(
    "lynex_event_queue_latency_seconds",
    "Time events spend in queue before processing",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)

# =============================================================================
# Token Usage Metrics (Critical for billing)
# =============================================================================

# Total tokens processed
tokens_processed_total = Counter(
    "lynex_tokens_processed_total",
    "Total number of tokens processed",
    ["project_id", "model", "token_type"],  # token_type: input, output
    registry=REGISTRY,
)

# Estimated cost
cost_usd_total = Counter(
    "lynex_cost_usd_total",
    "Total estimated cost in USD",
    ["project_id", "model"],
    registry=REGISTRY,
)

# =============================================================================
# Model Performance Metrics
# =============================================================================

# Model latency
model_latency = Histogram(
    "lynex_model_latency_seconds",
    "LLM model response latency",
    ["project_id", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)

# Model errors
model_errors_total = Counter(
    "lynex_model_errors_total",
    "Total number of model errors",
    ["project_id", "model", "error_type"],
    registry=REGISTRY,
)

# Model success rate (calculated metric)
model_requests_total = Counter(
    "lynex_model_requests_total",
    "Total number of model requests",
    ["project_id", "model", "status"],  # status: success, error
    registry=REGISTRY,
)

# =============================================================================
# Alert Metrics
# =============================================================================

# Alerts triggered
alerts_triggered_total = Counter(
    "lynex_alerts_triggered_total",
    "Total number of alerts triggered",
    ["project_id", "alert_rule_id", "severity"],
    registry=REGISTRY,
)

# Alert evaluation duration
alert_evaluation_duration = Histogram(
    "lynex_alert_evaluation_duration_seconds",
    "Time spent evaluating alert rules",
    buckets=(0.001, 0.01, 0.1, 0.5, 1.0),
    registry=REGISTRY,
)

# =============================================================================
# ClickHouse Metrics
# =============================================================================

# ClickHouse queries
clickhouse_queries_total = Counter(
    "lynex_clickhouse_queries_total",
    "Total number of ClickHouse queries",
    ["operation", "status"],  # operation: insert, select, delete
    registry=REGISTRY,
)

# ClickHouse query duration
clickhouse_query_duration = Histogram(
    "lynex_clickhouse_query_duration_seconds",
    "ClickHouse query duration",
    ["operation"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
    registry=REGISTRY,
)

# ClickHouse connection pool
clickhouse_connections = Gauge(
    "lynex_clickhouse_connections",
    "Number of active ClickHouse connections",
    registry=REGISTRY,
)

# =============================================================================
# S3 Archive Metrics
# =============================================================================

# Events archived
events_archived_total = Counter(
    "lynex_events_archived_total",
    "Total number of events archived to S3",
    ["status"],  # status: success, error
    registry=REGISTRY,
)

# Archive duration
archive_duration = Histogram(
    "lynex_archive_duration_seconds",
    "Time spent archiving events to S3",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0),
    registry=REGISTRY,
)

# Archive batch size
archive_batch_size = Histogram(
    "lynex_archive_batch_size",
    "Number of events in each archive batch",
    buckets=(100, 1000, 5000, 10000, 50000),
    registry=REGISTRY,
)

# S3 upload errors
s3_upload_errors_total = Counter(
    "lynex_s3_upload_errors_total",
    "Total number of S3 upload errors",
    ["error_type"],
    registry=REGISTRY,
)

# =============================================================================
# Redis Metrics
# =============================================================================

# Redis operations
redis_operations_total = Counter(
    "lynex_redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"],
    registry=REGISTRY,
)

# Redis connection pool
redis_connections = Gauge(
    "lynex_redis_connections",
    "Number of active Redis connections",
    registry=REGISTRY,
)

# =============================================================================
# System Metrics
# =============================================================================

# Service uptime
service_uptime_seconds = Gauge(
    "lynex_service_uptime_seconds",
    "Service uptime in seconds",
    registry=REGISTRY,
)

# Memory usage (if available)
memory_usage_bytes = Gauge(
    "lynex_memory_usage_bytes",
    "Memory usage in bytes",
    registry=REGISTRY,
)

# Active workers
active_workers = Gauge(
    "lynex_active_workers",
    "Number of active worker threads/processes",
    registry=REGISTRY,
)

# =============================================================================
# Custom Metrics Helpers
# =============================================================================

def track_event_processed(project_id: str, event_type: str, status: str = "success"):
    """Track a processed event."""
    events_processed_total.labels(
        project_id=project_id,
        event_type=event_type,
        status=status,
    ).inc()


def track_event_processing_time(event_type: str, duration_seconds: float):
    """Track event processing duration."""
    event_processing_duration.labels(event_type=event_type).observe(duration_seconds)


def track_token_usage(project_id: str, model: str, input_tokens: int, output_tokens: int):
    """Track token usage for billing."""
    tokens_processed_total.labels(
        project_id=project_id,
        model=model,
        token_type="input",
    ).inc(input_tokens)
    
    tokens_processed_total.labels(
        project_id=project_id,
        model=model,
        token_type="output",
    ).inc(output_tokens)


def track_cost(project_id: str, model: str, cost_usd: float):
    """Track estimated cost."""
    cost_usd_total.labels(
        project_id=project_id,
        model=model,
    ).inc(cost_usd)


def track_model_latency(project_id: str, model: str, latency_seconds: float):
    """Track model response latency."""
    model_latency.labels(
        project_id=project_id,
        model=model,
    ).observe(latency_seconds)


def track_model_request(project_id: str, model: str, success: bool):
    """Track model request success/failure."""
    status = "success" if success else "error"
    model_requests_total.labels(
        project_id=project_id,
        model=model,
        status=status,
    ).inc()


def track_alert_triggered(project_id: str, alert_rule_id: str, severity: str):
    """Track alert trigger."""
    alerts_triggered_total.labels(
        project_id=project_id,
        alert_rule_id=alert_rule_id,
        severity=severity,
    ).inc()


def track_clickhouse_query(operation: str, duration_seconds: float, success: bool = True):
    """Track ClickHouse query."""
    status = "success" if success else "error"
    clickhouse_queries_total.labels(operation=operation, status=status).inc()
    clickhouse_query_duration.labels(operation=operation).observe(duration_seconds)


def track_archive(events_count: int, duration_seconds: float, success: bool = True):
    """Track S3 archive operation."""
    status = "success" if success else "error"
    events_archived_total.labels(status=status).inc(events_count)
    archive_duration.observe(duration_seconds)
    archive_batch_size.observe(events_count)


def track_s3_error(error_type: str):
    """Track S3 upload error."""
    s3_upload_errors_total.labels(error_type=error_type).inc()


# =============================================================================
# Metrics Export
# =============================================================================

def get_metrics() -> bytes:
    """
    Generate Prometheus metrics in text format.
    Use this in FastAPI endpoints.
    """
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

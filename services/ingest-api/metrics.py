"""
Prometheus Metrics for Ingest API
Tracks ingestion performance, queue depth, and error rates.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)

# Create a custom registry
REGISTRY = CollectorRegistry()

# =============================================================================
# Application Info
# =============================================================================

app_info = Info(
    "lynex_ingest_app",
    "Lynex Ingest API information",
    registry=REGISTRY,
)
app_info.info({
    "version": "1.0.0",
    "service": "ingest-api",
})

# =============================================================================
# Ingestion Metrics
# =============================================================================

# Events received
events_received_total = Counter(
    "lynex_ingest_events_received_total",
    "Total number of events received",
    ["project_id", "event_type"],
    registry=REGISTRY,
)

# Events queued successfully
events_queued_total = Counter(
    "lynex_ingest_events_queued_total",
    "Total number of events queued to Redis",
    ["project_id", "status"],  # status: success, error
    registry=REGISTRY,
)

# Ingestion latency (time from request to queue)
ingestion_latency = Histogram(
    "lynex_ingest_latency_seconds",
    "Time from event receipt to queue",
    ["event_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=REGISTRY,
)

# Validation errors
validation_errors_total = Counter(
    "lynex_ingest_validation_errors_total",
    "Total number of validation errors",
    ["error_type"],
    registry=REGISTRY,
)

# =============================================================================
# Queue Metrics
# =============================================================================

# Queue depth
queue_depth = Gauge(
    "lynex_ingest_queue_depth",
    "Number of events in Redis queue",
    registry=REGISTRY,
)

# Queue latency (pending time)
queue_latency = Histogram(
    "lynex_ingest_queue_latency_seconds",
    "Time events spend in queue",
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)

# =============================================================================
# Rate Limiting Metrics
# =============================================================================

# Rate limit hits
rate_limit_hits_total = Counter(
    "lynex_ingest_rate_limit_hits_total",
    "Total number of rate limit rejections",
    ["project_id"],
    registry=REGISTRY,
)

# =============================================================================
# Redis Metrics
# =============================================================================

# Redis operations
redis_operations_total = Counter(
    "lynex_ingest_redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"],
    registry=REGISTRY,
)

# Redis connection pool
redis_connections = Gauge(
    "lynex_ingest_redis_connections",
    "Number of active Redis connections",
    registry=REGISTRY,
)

# =============================================================================
# HTTP Metrics
# =============================================================================

# HTTP requests
http_requests_total = Counter(
    "lynex_ingest_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
    registry=REGISTRY,
)

# HTTP request duration
http_request_duration = Histogram(
    "lynex_ingest_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=REGISTRY,
)

# =============================================================================
# Helper Functions
# =============================================================================

def track_event_received(project_id: str, event_type: str):
    """Track an event received."""
    events_received_total.labels(
        project_id=project_id,
        event_type=event_type,
    ).inc()


def track_event_queued(project_id: str, success: bool = True):
    """Track an event queued to Redis."""
    status = "success" if success else "error"
    events_queued_total.labels(
        project_id=project_id,
        status=status,
    ).inc()


def track_ingestion_latency(event_type: str, duration_seconds: float):
    """Track ingestion latency."""
    ingestion_latency.labels(event_type=event_type).observe(duration_seconds)


def track_validation_error(error_type: str):
    """Track a validation error."""
    validation_errors_total.labels(error_type=error_type).inc()


def track_rate_limit_hit(project_id: str):
    """Track a rate limit rejection."""
    rate_limit_hits_total.labels(project_id=project_id).inc()


def track_http_request(method: str, path: str, status_code: int, duration_seconds: float):
    """Track HTTP request."""
    http_requests_total.labels(
        method=method,
        path=path,
        status_code=status_code,
    ).inc()
    
    http_request_duration.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)


def update_queue_depth(depth: int):
    """Update queue depth gauge."""
    queue_depth.set(depth)


def update_redis_connections(count: int):
    """Update Redis connection count."""
    redis_connections.set(count)


# =============================================================================
# Metrics Export
# =============================================================================

def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

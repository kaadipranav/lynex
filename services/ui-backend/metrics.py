"""
Prometheus Metrics for UI Backend
Tracks query performance, cache hits, and API usage.
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
    "lynex_ui_backend_app",
    "Lynex UI Backend API information",
    registry=REGISTRY,
)
app_info.info({
    "version": "1.0.0",
    "service": "ui-backend",
})

# =============================================================================
# Query Metrics
# =============================================================================

# Queries executed
queries_executed_total = Counter(
    "lynex_ui_queries_executed_total",
    "Total number of queries executed",
    ["project_id", "query_type"],
    registry=REGISTRY,
)

# Query latency
query_latency = Histogram(
    "lynex_ui_query_latency_seconds",
    "Query execution time",
    ["query_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
    registry=REGISTRY,
)

# Query errors
query_errors_total = Counter(
    "lynex_ui_query_errors_total",
    "Total number of query errors",
    ["query_type", "error_type"],
    registry=REGISTRY,
)

# =============================================================================
# Cache Metrics
# =============================================================================

# Cache hits/misses
cache_operations_total = Counter(
    "lynex_ui_cache_operations_total",
    "Total number of cache operations",
    ["operation"],  # operation: hit, miss, set, delete
    registry=REGISTRY,
)

# Cache latency
cache_latency = Histogram(
    "lynex_ui_cache_latency_seconds",
    "Cache operation latency",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1),
    registry=REGISTRY,
)

# =============================================================================
# API Usage Metrics
# =============================================================================

# API requests by endpoint
api_requests_total = Counter(
    "lynex_ui_api_requests_total",
    "Total API requests",
    ["project_id", "endpoint", "method", "status_code"],
    registry=REGISTRY,
)

# API latency
api_latency = Histogram(
    "lynex_ui_api_latency_seconds",
    "API request latency",
    ["endpoint", "method"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=REGISTRY,
)

# =============================================================================
# Authentication Metrics
# =============================================================================

# Auth requests
auth_requests_total = Counter(
    "lynex_ui_auth_requests_total",
    "Total authentication requests",
    ["method", "status"],  # method: jwt, api_key, supabase; status: success, failure
    registry=REGISTRY,
)

# =============================================================================
# Database Metrics
# =============================================================================

# ClickHouse queries
clickhouse_queries_total = Counter(
    "lynex_ui_clickhouse_queries_total",
    "Total ClickHouse queries",
    ["query_type", "status"],
    registry=REGISTRY,
)

# ClickHouse query latency
clickhouse_query_latency = Histogram(
    "lynex_ui_clickhouse_query_latency_seconds",
    "ClickHouse query latency",
    ["query_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
    registry=REGISTRY,
)

# MongoDB operations
mongodb_operations_total = Counter(
    "lynex_ui_mongodb_operations_total",
    "Total MongoDB operations",
    ["operation", "collection", "status"],
    registry=REGISTRY,
)

# =============================================================================
# Helper Functions
# =============================================================================

def track_query(project_id: str, query_type: str, duration_seconds: float, success: bool = True):
    """Track a query execution."""
    queries_executed_total.labels(
        project_id=project_id,
        query_type=query_type,
    ).inc()
    
    query_latency.labels(query_type=query_type).observe(duration_seconds)
    
    if not success:
        query_errors_total.labels(
            query_type=query_type,
            error_type="execution_error",
        ).inc()


def track_cache_operation(operation: str, duration_seconds: float = 0):
    """Track a cache operation."""
    cache_operations_total.labels(operation=operation).inc()
    if duration_seconds > 0:
        cache_latency.labels(operation=operation).observe(duration_seconds)


def track_api_request(project_id: str, endpoint: str, method: str, status_code: int, duration_seconds: float):
    """Track an API request."""
    api_requests_total.labels(
        project_id=project_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
    ).inc()
    
    api_latency.labels(
        endpoint=endpoint,
        method=method,
    ).observe(duration_seconds)


def track_auth_request(method: str, success: bool):
    """Track an authentication request."""
    status = "success" if success else "failure"
    auth_requests_total.labels(
        method=method,
        status=status,
    ).inc()


def track_clickhouse_query(query_type: str, duration_seconds: float, success: bool = True):
    """Track a ClickHouse query."""
    status = "success" if success else "error"
    clickhouse_queries_total.labels(
        query_type=query_type,
        status=status,
    ).inc()
    
    clickhouse_query_latency.labels(query_type=query_type).observe(duration_seconds)


def track_mongodb_operation(operation: str, collection: str, success: bool = True):
    """Track a MongoDB operation."""
    status = "success" if success else "error"
    mongodb_operations_total.labels(
        operation=operation,
        collection=collection,
        status=status,
    ).inc()


# =============================================================================
# Metrics Export
# =============================================================================

def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

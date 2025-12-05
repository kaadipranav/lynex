# Prometheus Metrics - Monitoring Guide

## Overview

All Lynex services expose Prometheus metrics at `/metrics` endpoints for comprehensive observability. This is a **critical enterprise requirement** - 80% of RFPs mandate Prometheus-compatible monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Metrics Collection Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Application Code → prometheus_client → /metrics endpoint    │
│                                                ↓                 │
│  2. Prometheus Server → Scrape /metrics every 15s               │
│                                                ↓                 │
│  3. Prometheus → Store in TSDB (Time-Series Database)           │
│                                                ↓                 │
│  4. Grafana → Query Prometheus → Display Dashboards             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Metrics Endpoints

| Service | Endpoint | Port |
|---------|----------|------|
| Ingest API | `http://localhost:8001/metrics` | 8001 |
| UI Backend | `http://localhost:8000/metrics` | 8000 |
| Processor | *(No HTTP endpoint - exports via registry)* | N/A |

## Available Metrics

### 1. Ingest API Metrics

#### Event Ingestion
```promql
# Total events received
lynex_ingest_events_received_total{project_id="proj-123", event_type="log"}

# Events successfully queued
lynex_ingest_events_queued_total{project_id="proj-123", status="success"}

# Ingestion latency (95th percentile)
histogram_quantile(0.95, rate(lynex_ingest_latency_seconds_bucket[5m]))
```

#### Queue Monitoring
```promql
# Current queue depth
lynex_ingest_queue_depth

# Queue latency (time in queue before processing)
histogram_quantile(0.95, rate(lynex_ingest_queue_latency_seconds_bucket[5m]))
```

#### Rate Limiting
```promql
# Rate limit rejections per project
rate(lynex_ingest_rate_limit_hits_total{project_id="proj-123"}[5m])
```

#### Validation Errors
```promql
# Validation errors by type
rate(lynex_ingest_validation_errors_total{error_type="schema_invalid"}[5m])
```

### 2. UI Backend Metrics

#### Query Performance
```promql
# Total queries executed
lynex_ui_queries_executed_total{project_id="proj-123", query_type="events"}

# Query latency (95th percentile)
histogram_quantile(0.95, rate(lynex_ui_query_latency_seconds_bucket{query_type="events"}[5m]))

# Query errors
rate(lynex_ui_query_errors_total{query_type="events"}[5m])
```

#### Cache Performance
```promql
# Cache hit rate
rate(lynex_ui_cache_operations_total{operation="hit"}[5m]) / 
rate(lynex_ui_cache_operations_total[5m])

# Cache operations
rate(lynex_ui_cache_operations_total{operation="hit"}[5m])
rate(lynex_ui_cache_operations_total{operation="miss"}[5m])
```

#### API Usage
```promql
# Requests per second by endpoint
rate(lynex_ui_api_requests_total{endpoint="/api/v1/events"}[1m])

# Error rate (4xx + 5xx)
rate(lynex_ui_api_requests_total{status_code=~"4..|5.."}[5m])
```

#### Authentication
```promql
# Auth failures
rate(lynex_ui_auth_requests_total{status="failure"}[5m])

# Auth success rate
rate(lynex_ui_auth_requests_total{status="success"}[5m]) /
rate(lynex_ui_auth_requests_total[5m])
```

### 3. Processor Metrics

#### Event Processing
```promql
# Events processed per second
rate(lynex_events_processed_total{status="success"}[1m])

# Processing latency (95th percentile)
histogram_quantile(0.95, rate(lynex_event_processing_duration_seconds_bucket[5m]))

# Event queue depth (waiting to be processed)
lynex_event_queue_depth

# Queue latency
histogram_quantile(0.95, rate(lynex_event_queue_latency_seconds_bucket[5m]))
```

#### Token Usage & Billing
```promql
# Total tokens processed per hour
increase(lynex_tokens_processed_total{model="gpt-4", token_type="input"}[1h])
increase(lynex_tokens_processed_total{model="gpt-4", token_type="output"}[1h])

# Cost per project (24 hours)
increase(lynex_cost_usd_total{project_id="proj-123"}[24h])

# Cost rate ($/hour)
rate(lynex_cost_usd_total[1h])
```

#### Model Performance
```promql
# Model latency (95th percentile)
histogram_quantile(0.95, rate(lynex_model_latency_seconds_bucket{model="gpt-4"}[5m]))

# Model error rate
rate(lynex_model_errors_total{model="gpt-4"}[5m])

# Model success rate
rate(lynex_model_requests_total{model="gpt-4", status="success"}[5m]) /
rate(lynex_model_requests_total{model="gpt-4"}[5m])
```

#### Alerts
```promql
# Alerts triggered per hour
increase(lynex_alerts_triggered_total{severity="critical"}[1h])

# Alert evaluation duration
histogram_quantile(0.95, rate(lynex_alert_evaluation_duration_seconds_bucket[5m]))
```

#### ClickHouse
```promql
# ClickHouse operations per second
rate(lynex_clickhouse_queries_total{operation="insert"}[1m])

# ClickHouse query latency
histogram_quantile(0.95, rate(lynex_clickhouse_query_duration_seconds_bucket{operation="select"}[5m]))

# ClickHouse error rate
rate(lynex_clickhouse_queries_total{status="error"}[5m])
```

#### S3 Archival
```promql
# Events archived per day
increase(lynex_events_archived_total{status="success"}[24h])

# Archive job duration
histogram_quantile(0.95, rate(lynex_archive_duration_seconds_bucket[24h]))

# Archive batch size
histogram_quantile(0.95, rate(lynex_archive_batch_size_bucket[24h]))

# S3 upload errors
rate(lynex_s3_upload_errors_total[1h])
```

## Prometheus Configuration

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Ingest API
  - job_name: 'lynex-ingest-api'
    static_configs:
      - targets: ['localhost:8001']
        labels:
          service: 'ingest-api'
          environment: 'production'
    metrics_path: '/metrics'
    scrape_interval: 15s

  # UI Backend
  - job_name: 'lynex-ui-backend'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          service: 'ui-backend'
          environment: 'production'
    metrics_path: '/metrics'
    scrape_interval: 15s

  # For Kubernetes deployments
  - job_name: 'lynex-k8s'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  prometheus-data:
  grafana-data:
```

## Grafana Dashboards

### 1. System Overview Dashboard

**Panels:**
- Total Events Processed (last 24h)
- Current Queue Depth
- Ingestion Rate (events/sec)
- Processing Latency (p95)
- Error Rate
- Active Alerts

**Query Examples:**
```promql
# Events processed (24h)
increase(lynex_events_processed_total{status="success"}[24h])

# Current queue depth
lynex_event_queue_depth

# Ingestion rate
rate(lynex_ingest_events_received_total[5m])

# Processing latency p95
histogram_quantile(0.95, rate(lynex_event_processing_duration_seconds_bucket[5m]))

# Error rate
rate(lynex_events_processed_total{status="error"}[5m])
```

### 2. Cost & Token Usage Dashboard

**Panels:**
- Total Cost (Today / This Month)
- Cost by Model (Pie Chart)
- Tokens Processed by Model
- Cost Rate ($/hour)
- Top Projects by Cost

**Query Examples:**
```promql
# Total cost today
increase(lynex_cost_usd_total[24h])

# Cost by model (pie chart)
sum by (model) (increase(lynex_cost_usd_total[24h]))

# Tokens by model
sum by (model, token_type) (increase(lynex_tokens_processed_total[1h]))

# Cost rate
rate(lynex_cost_usd_total[1h])

# Top projects
topk(10, sum by (project_id) (increase(lynex_cost_usd_total[24h])))
```

### 3. Model Performance Dashboard

**Panels:**
- Model Latency (p50, p95, p99)
- Model Success Rate
- Model Errors by Type
- Requests per Model
- Model Latency Heatmap

**Query Examples:**
```promql
# Latency percentiles
histogram_quantile(0.50, rate(lynex_model_latency_seconds_bucket[5m]))
histogram_quantile(0.95, rate(lynex_model_latency_seconds_bucket[5m]))
histogram_quantile(0.99, rate(lynex_model_latency_seconds_bucket[5m]))

# Success rate
sum(rate(lynex_model_requests_total{status="success"}[5m])) by (model) /
sum(rate(lynex_model_requests_total[5m])) by (model)

# Error breakdown
sum by (model, error_type) (rate(lynex_model_errors_total[5m]))
```

### 4. Infrastructure Dashboard

**Panels:**
- ClickHouse Query Latency
- Redis Operations/sec
- S3 Archive Status
- Service Uptime
- Memory Usage
- Active Connections

**Query Examples:**
```promql
# ClickHouse latency
histogram_quantile(0.95, rate(lynex_clickhouse_query_duration_seconds_bucket[5m]))

# Redis ops
rate(lynex_redis_operations_total[1m])

# Archive success rate
rate(lynex_events_archived_total{status="success"}[1h]) /
rate(lynex_events_archived_total[1h])

# Service uptime
lynex_service_uptime_seconds
```

## Alerting Rules

### alerts.yml

```yaml
groups:
  - name: lynex_critical
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(lynex_events_processed_total{status="error"}[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High event processing error rate"
          description: "Error rate is {{ $value }} errors/sec for {{ $labels.project_id }}"

      # Queue backlog
      - alert: QueueBacklog
        expr: lynex_event_queue_depth > 10000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Event queue backlog detected"
          description: "Queue depth is {{ $value }} events"

      # High latency
      - alert: HighProcessingLatency
        expr: histogram_quantile(0.95, rate(lynex_event_processing_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High processing latency"
          description: "P95 latency is {{ $value }}s"

      # ClickHouse down
      - alert: ClickHouseDown
        expr: up{job="clickhouse"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "ClickHouse is down"

      # Cost spike
      - alert: CostSpike
        expr: rate(lynex_cost_usd_total[1h]) > 100
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Unusual cost spike detected"
          description: "Cost rate is ${{ $value }}/hour"

      # Model errors
      - alert: HighModelErrorRate
        expr: rate(lynex_model_errors_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High model error rate"
          description: "{{ $labels.model }} error rate: {{ $value }} errors/sec"

      # Archive failures
      - alert: ArchiveFailures
        expr: rate(lynex_events_archived_total{status="error"}[1h]) > 0
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "S3 archive failures detected"
```

## Testing Metrics

### Manual Testing

```bash
# Check metrics endpoint
curl http://localhost:8001/metrics

# Check specific metric
curl http://localhost:8001/metrics | grep lynex_ingest_events_received_total

# Prometheus query (if Prometheus is running)
curl 'http://localhost:9090/api/v1/query?query=lynex_event_queue_depth'
```

### Load Testing with Metrics

```python
import requests
import time

# Generate load
for i in range(1000):
    requests.post("http://localhost:8001/api/v1/events", json={
        "event_id": f"test-{i}",
        "type": "log",
        "body": {"message": f"Test event {i}"},
    })
    time.sleep(0.01)

# Check metrics
response = requests.get("http://localhost:8001/metrics")
print(response.text)
```

## Production Checklist

- [ ] Prometheus server deployed and scraping all services
- [ ] Grafana dashboards imported and tested
- [ ] Alert rules configured in Prometheus
- [ ] Alertmanager configured (Slack/PagerDuty/Email)
- [ ] Metrics retention set (30+ days recommended)
- [ ] Grafana authentication enabled
- [ ] Metrics endpoints not exposed publicly (use internal network)
- [ ] Service discovery configured (Kubernetes/Consul)
- [ ] Backup strategy for Prometheus TSDB

## Common Queries

### SLA Monitoring

```promql
# Availability (99.9% target)
sum(rate(lynex_ui_api_requests_total{status_code!~"5.."}[5m])) /
sum(rate(lynex_ui_api_requests_total[5m]))

# Latency SLA (p95 < 500ms)
histogram_quantile(0.95, rate(lynex_ui_api_latency_seconds_bucket[5m])) < 0.5
```

### Capacity Planning

```promql
# Events per second (trend)
rate(lynex_ingest_events_received_total[1h])

# Storage growth rate
rate(lynex_events_processed_total[24h]) * 365

# Cost projection
rate(lynex_cost_usd_total[7d]) * 30
```

### Debugging

```promql
# Slow queries
topk(10, max by (query_type) (lynex_ui_query_latency_seconds))

# Failed operations by type
topk(10, sum by (operation, status) (rate(lynex_clickhouse_queries_total{status="error"}[5m])))

# Rate limit victims
topk(10, sum by (project_id) (rate(lynex_ingest_rate_limit_hits_total[1h])))
```

## Integration with External Systems

### Datadog
```yaml
# datadog-agent.yaml
- prometheus_url: http://lynex-ingest-api:8001/metrics
  namespace: lynex
  metrics:
    - lynex_*
```

### New Relic
```yaml
# newrelic-infrastructure.yml
integrations:
  - name: nri-prometheus
    config:
      urls:
        - http://lynex-ingest-api:8001/metrics
```

### CloudWatch (AWS)
```bash
# Use CloudWatch Agent with Prometheus scraping
aws cloudwatch put-metric-data \
  --namespace Lynex \
  --metric-name EventsProcessed \
  --value $(curl -s http://localhost:8001/metrics | grep lynex_events_processed_total | awk '{print $2}')
```

## Troubleshooting

### No metrics appearing

1. Check `/metrics` endpoint is accessible
2. Verify Prometheus scrape config
3. Check Prometheus logs: `docker logs prometheus`
4. Verify network connectivity

### High cardinality warnings

Limit label values in metrics:
```python
# BAD: Unbounded user_id labels
user_requests_total.labels(user_id="user-12345").inc()

# GOOD: Use project_id only
project_requests_total.labels(project_id="proj-123").inc()
```

### Missing data

1. Check retention settings in Prometheus
2. Verify scrape interval matches query range
3. Check for service restarts (metrics reset)

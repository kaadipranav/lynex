-- ============================================================================
-- Sentry for AI - ClickHouse Schema
-- ============================================================================
-- Run this against your ClickHouse instance to create the tables.
-- 
-- For Aiven/Tinybird: Use their web console to run these statements.
-- For self-hosted: clickhouse-client < schema.sql
-- ============================================================================


-- ============================================================================
-- EVENTS TABLE (Main event storage)
-- ============================================================================
-- Stores all ingested events. Uses MergeTree for efficient time-series queries.

CREATE TABLE IF NOT EXISTS events (
    -- Core identifiers
    event_id UUID,
    project_id String,
    
    -- Event metadata
    type LowCardinality(String),  -- log, error, span, token_usage, etc.
    timestamp DateTime64(3),       -- Event timestamp (millisecond precision)
    
    -- SDK info
    sdk_name LowCardinality(String),
    sdk_version String,
    
    -- Event body (stored as JSON string for flexibility)
    body String,
    
    -- Optional context
    context String DEFAULT '{}',
    
    -- Processing metadata
    queued_at DateTime64(3),
    processed_at DateTime64(3) DEFAULT now64(3),
    queue_latency_ms Float32 DEFAULT 0,
    
    -- Cost tracking (for token_usage events)
    estimated_cost_usd Float64 DEFAULT 0,
    
    -- Partitioning and sorting
    _date Date DEFAULT toDate(timestamp),
    _hour DateTime DEFAULT toStartOfHour(timestamp)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)  -- Monthly partitions
ORDER BY (project_id, type, timestamp, event_id)
TTL _date + INTERVAL 30 DAY   -- Auto-delete after 30 days (configurable)
SETTINGS index_granularity = 8192;


-- ============================================================================
-- TOKEN USAGE AGGREGATES (Materialized View)
-- ============================================================================
-- Pre-aggregates token usage for fast dashboard queries.

CREATE TABLE IF NOT EXISTS token_usage_hourly (
    project_id String,
    model LowCardinality(String),
    hour DateTime,
    
    -- Aggregates
    total_input_tokens UInt64,
    total_output_tokens UInt64,
    total_cost_usd Float64,
    request_count UInt64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (project_id, model, hour);

-- Materialized view to auto-populate token_usage_hourly
CREATE MATERIALIZED VIEW IF NOT EXISTS token_usage_hourly_mv
TO token_usage_hourly
AS SELECT
    project_id,
    JSONExtractString(body, 'model') AS model,
    toStartOfHour(timestamp) AS hour,
    JSONExtractUInt(body, 'inputTokens') AS total_input_tokens,
    JSONExtractUInt(body, 'outputTokens') AS total_output_tokens,
    estimated_cost_usd AS total_cost_usd,
    1 AS request_count
FROM events
WHERE type = 'token_usage';


-- ============================================================================
-- ERROR AGGREGATES (Materialized View)
-- ============================================================================
-- Pre-aggregates errors for fast alerting and dashboard queries.

CREATE TABLE IF NOT EXISTS errors_hourly (
    project_id String,
    hour DateTime,
    error_message String,
    
    -- Aggregates
    error_count UInt64,
    first_seen DateTime,
    last_seen DateTime
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (project_id, hour, error_message);

CREATE MATERIALIZED VIEW IF NOT EXISTS errors_hourly_mv
TO errors_hourly
AS SELECT
    project_id,
    toStartOfHour(timestamp) AS hour,
    JSONExtractString(body, 'message') AS error_message,
    1 AS error_count,
    timestamp AS first_seen,
    timestamp AS last_seen
FROM events
WHERE type = 'error';


-- ============================================================================
-- REQUEST STATS (Materialized View)
-- ============================================================================
-- General request statistics per project.

CREATE TABLE IF NOT EXISTS request_stats_hourly (
    project_id String,
    hour DateTime,
    event_type LowCardinality(String),
    
    -- Aggregates
    event_count UInt64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (project_id, hour, event_type);

CREATE MATERIALIZED VIEW IF NOT EXISTS request_stats_hourly_mv
TO request_stats_hourly
AS SELECT
    project_id,
    toStartOfHour(timestamp) AS hour,
    type AS event_type,
    1 AS event_count
FROM events;


-- ============================================================================
-- LATENCY STATS (For model_response events)
-- ============================================================================

CREATE TABLE IF NOT EXISTS latency_stats_hourly (
    project_id String,
    model LowCardinality(String),
    hour DateTime,
    
    -- Aggregates
    total_latency_ms UInt64,
    request_count UInt64,
    min_latency_ms UInt32,
    max_latency_ms UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (project_id, model, hour);

CREATE MATERIALIZED VIEW IF NOT EXISTS latency_stats_hourly_mv
TO latency_stats_hourly
AS SELECT
    project_id,
    JSONExtractString(body, 'model') AS model,
    toStartOfHour(timestamp) AS hour,
    JSONExtractUInt(body, 'latencyMs') AS total_latency_ms,
    1 AS request_count,
    JSONExtractUInt(body, 'latencyMs') AS min_latency_ms,
    JSONExtractUInt(body, 'latencyMs') AS max_latency_ms
FROM events
WHERE type = 'model_response';


-- ============================================================================
-- USEFUL QUERIES (Examples)
-- ============================================================================

-- Get events for a project (last 24 hours)
-- SELECT * FROM events 
-- WHERE project_id = 'proj_demo' 
--   AND timestamp > now() - INTERVAL 24 HOUR
-- ORDER BY timestamp DESC
-- LIMIT 100;

-- Get token usage summary
-- SELECT 
--     model,
--     sum(total_input_tokens) as input_tokens,
--     sum(total_output_tokens) as output_tokens,
--     sum(total_cost_usd) as total_cost
-- FROM token_usage_hourly
-- WHERE project_id = 'proj_demo'
--   AND hour > now() - INTERVAL 7 DAY
-- GROUP BY model;

-- Get error rate
-- SELECT 
--     toStartOfHour(timestamp) as hour,
--     countIf(type = 'error') as errors,
--     count() as total,
--     errors / total * 100 as error_rate_pct
-- FROM events
-- WHERE project_id = 'proj_demo'
--   AND timestamp > now() - INTERVAL 24 HOUR
-- GROUP BY hour
-- ORDER BY hour;

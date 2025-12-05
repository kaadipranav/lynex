# S3 Cold Storage - Architecture & Setup

## Overview

The S3 Cold Storage system automatically archives ClickHouse events older than 30 days to Amazon S3 in Parquet format. This reduces ClickHouse storage costs by 80%+ while maintaining compliance and data integrity.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Event Lifecycle                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Ingest → Redis → Processor → ClickHouse (Hot Storage)      │
│                                       ↓                          │
│                                  30 days                         │
│                                       ↓                          │
│  2. S3 Archiver → Query Old Events → Archive to S3/Parquet     │
│                                       ↓                          │
│  3. DELETE from ClickHouse (optional but recommended)           │
│                                       ↓                          │
│  4. S3 Lifecycle → Move to Glacier (long-term retention)        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Cost Savings

| Storage Tier | Cost (per GB/month) | Use Case |
|--------------|---------------------|----------|
| ClickHouse | $0.25 - $0.50 | Last 30 days (hot queries) |
| S3 Standard-IA | $0.0125 | 30-90 days (cold archive) |
| S3 Glacier | $0.004 | 90+ days (compliance) |

**Example savings for 1TB/month ingestion:**
- ClickHouse only: $250/month
- With S3 archival: $50/month (80% savings)

## Setup

### 1. AWS Configuration

Create an S3 bucket and IAM user with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::lynex-cold-storage",
        "arn:aws:s3:::lynex-cold-storage/*"
      ]
    }
  ]
}
```

### 2. Environment Variables

Add to `.env`:

```bash
# S3 Cold Storage
S3_ARCHIVE_BUCKET=lynex-cold-storage
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Archive configuration
ARCHIVE_AFTER_DAYS=30
DELETE_AFTER_ARCHIVE=true
ARCHIVE_BATCH_SIZE=10000
ARCHIVE_INTERVAL_HOURS=24
```

### 3. S3 Lifecycle Policy (Optional)

Move archived data to Glacier after 90 days:

```json
{
  "Rules": [
    {
      "Id": "MoveToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Filter": {
        "Prefix": "events/"
      }
    }
  ]
}
```

### 4. ClickHouse TTL (Already configured)

The ClickHouse `events` table already has a 30-day TTL:

```sql
TTL _date + INTERVAL 30 DAY
```

This serves as a **backup deletion** if S3 archival fails.

## How It Works

### Archival Process

1. **Background Job**: Runs every 24 hours (configurable via `ARCHIVE_INTERVAL_HOURS`)
2. **Query Old Events**: Selects events older than 30 days from ClickHouse
3. **Convert to Parquet**: Uses PyArrow to compress events efficiently
4. **Upload to S3**: Stores in `s3://bucket/events/YYYY-MM/events_TIMESTAMP.parquet`
5. **Delete from ClickHouse**: Removes archived events to free space

### File Structure

```
s3://lynex-cold-storage/
├── events/
│   ├── 2024-01/
│   │   ├── events_20240201_120000.parquet
│   │   └── events_20240201_180000.parquet
│   ├── 2024-02/
│   │   └── events_20240301_120000.parquet
│   └── 2024-03/
│       └── events_20240401_120000.parquet
```

### Data Schema

Parquet files preserve the full ClickHouse schema:

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | string | UUID |
| `project_id` | string | Project identifier |
| `type` | string | Event type (log, span, token_usage) |
| `timestamp` | timestamp(ms) | Event timestamp |
| `sdk_name` | string | SDK identifier |
| `sdk_version` | string | SDK version |
| `body` | string | JSON event body |
| `context` | string | JSON context metadata |
| `queued_at` | timestamp(ms) | Queue timestamp |
| `processed_at` | timestamp(ms) | Processing timestamp |
| `queue_latency_ms` | float32 | Queue latency |
| `estimated_cost_usd` | float64 | Token cost |

## Rehydration (Future Feature)

To query archived data, implement an S3 → ClickHouse rehydration flow:

```python
# Pseudocode for rehydration
async def rehydrate_archive(start_date, end_date):
    # List Parquet files in date range
    files = s3.list_objects(prefix=f"events/{start_date:%Y-%m}/")
    
    # Download and insert into temporary ClickHouse table
    for file in files:
        parquet_data = s3.get_object(file)
        clickhouse.insert("events_temp", parquet_data)
    
    # Query the temporary table
    results = clickhouse.query("SELECT * FROM events_temp WHERE ...")
    
    # Drop temporary table
    clickhouse.execute("DROP TABLE events_temp")
```

## Monitoring

### Logs

Watch for archival logs in processor service:

```bash
docker logs -f lynex-processor | grep "archiv"
```

Expected output:
```
🗄️  Starting S3 archival loop (every 24h)
📦 Found 10000 events to archive
✅ Uploaded to s3://lynex-cold-storage/events/2024-01/events_20240215_120000.parquet
🗑️  Deleted 10000 events from ClickHouse
✅ Archived 10000 events to S3
```

### Metrics (After Prometheus integration)

```promql
# Events archived per day
rate(lynex_events_archived_total[1d])

# Archive job duration
histogram_quantile(0.95, lynex_archive_duration_seconds)

# Failed archive attempts
rate(lynex_archive_errors_total[5m])
```

## Testing

### Unit Tests

```python
import pytest
from services.processor.s3_archiver import S3Archiver

@pytest.mark.asyncio
async def test_archive_old_events(clickhouse_mock, s3_mock):
    archiver = S3Archiver(clickhouse_mock)
    await archiver.archive_old_events()
    
    # Verify S3 upload
    assert s3_mock.put_object.called
    
    # Verify ClickHouse deletion
    assert clickhouse_mock.execute.called_with("DELETE FROM events...")
```

### Manual Testing

1. Insert test events with old timestamps:

```sql
INSERT INTO events (event_id, project_id, type, timestamp, ...)
VALUES ('test-123', 'proj-1', 'log', now() - INTERVAL 35 DAY, ...)
```

2. Run archival manually:

```python
python -c "
import asyncio
from processor.s3_archiver import get_archiver
from processor.clickhouse import ClickHouseClient

async def test():
    ch = ClickHouseClient()
    await ch.connect()
    archiver = get_archiver(ch)
    await archiver.archive_old_events()

asyncio.run(test())
"
```

3. Verify S3 upload:

```bash
aws s3 ls s3://lynex-cold-storage/events/ --recursive
```

## Troubleshooting

### Issue: "AccessDenied" errors

**Cause**: IAM user lacks S3 permissions

**Fix**: Add the IAM policy shown in Setup section

### Issue: "No events to archive"

**Cause**: All events are <30 days old or already archived

**Fix**: Wait for events to age or adjust `ARCHIVE_AFTER_DAYS`

### Issue: "ClickHouse DELETE failed"

**Cause**: User lacks DELETE permissions

**Fix**: Grant `ALTER TABLE` permission:

```sql
GRANT ALTER DELETE ON events TO lynex_user;
```

### Issue: Archive job takes too long

**Cause**: Large batch size or slow S3 uploads

**Fix**: Reduce `ARCHIVE_BATCH_SIZE` to 5000-10000

## Production Checklist

- [ ] S3 bucket created with encryption enabled
- [ ] IAM user with least-privilege permissions
- [ ] Environment variables configured
- [ ] S3 lifecycle policy for Glacier transition
- [ ] ClickHouse user has `ALTER DELETE` permission
- [ ] Monitoring alerts for archival failures
- [ ] Backup strategy for S3 data (versioning enabled)
- [ ] Test rehydration process documented

## Cost Calculator

Use this to estimate savings:

```
Monthly Ingestion Rate (GB): X
ClickHouse Cost ($/GB): 0.25
S3 Standard-IA Cost ($/GB): 0.0125

Without Archival: X * 0.25 * 12 months = $Y/year
With Archival: X * 0.25 + (X * 11) * 0.0125 = $Z/year

Savings: $Y - $Z = 80%+ reduction
```

**Example**: 100 GB/month ingestion
- Without archival: $300/year
- With archival: $51/year
- **Savings: $249/year (83%)**

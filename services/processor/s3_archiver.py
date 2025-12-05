"""
S3 Cold Storage Archiver
Archives ClickHouse events >30 days to S3/Parquet for cost savings.
Reduces ClickHouse storage costs by 80%+.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import io
import json

import boto3
from botocore.exceptions import ClientError
import pyarrow as pa
import pyarrow.parquet as pq
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from clickhouse import ClickHouseClient

logger = logging.getLogger("watchllm.processor.s3_archiver")


# =============================================================================
# S3 Archiver Configuration
# =============================================================================

class S3ArchiverConfig:
    """Configuration for S3 archiving."""
    
    # Archive events older than this many days
    ARCHIVE_AFTER_DAYS = int(os.getenv("ARCHIVE_AFTER_DAYS", "30"))
    
    # Delete from ClickHouse after archiving (recommended for cost savings)
    DELETE_AFTER_ARCHIVE = os.getenv("DELETE_AFTER_ARCHIVE", "true").lower() == "true"
    
    # S3 bucket configuration
    S3_BUCKET = os.getenv("S3_ARCHIVE_BUCKET", "lynex-cold-storage")
    S3_PREFIX = os.getenv("S3_ARCHIVE_PREFIX", "events")
    S3_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # AWS credentials (use IAM roles in production)
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # Batch size for archiving (events per Parquet file)
    BATCH_SIZE = int(os.getenv("ARCHIVE_BATCH_SIZE", "10000"))
    
    # Run archival job every N hours
    ARCHIVE_INTERVAL_HOURS = int(os.getenv("ARCHIVE_INTERVAL_HOURS", "24"))


# =============================================================================
# S3 Archiver
# =============================================================================

class S3Archiver:
    """
    Archives old events from ClickHouse to S3 in Parquet format.
    Automatically deletes archived data from ClickHouse to reduce costs.
    """
    
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse = clickhouse_client
        self.config = S3ArchiverConfig()
        
        # Initialize S3 client
        session_kwargs = {}
        if self.config.AWS_ACCESS_KEY_ID and self.config.AWS_SECRET_ACCESS_KEY:
            session_kwargs = {
                "aws_access_key_id": self.config.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": self.config.AWS_SECRET_ACCESS_KEY,
                "region_name": self.config.S3_REGION,
            }
        
        self.s3_client = boto3.client("s3", **session_kwargs)
        
        logger.info(
            f"S3 Archiver initialized: bucket={self.config.S3_BUCKET}, "
            f"archive_after={self.config.ARCHIVE_AFTER_DAYS}d, "
            f"delete_after_archive={self.config.DELETE_AFTER_ARCHIVE}"
        )
    
    async def start_archival_loop(self):
        """
        Run archival job periodically.
        This should be called as a background task.
        """
        logger.info(
            f"🗄️  Starting S3 archival loop (every {self.config.ARCHIVE_INTERVAL_HOURS}h)"
        )
        
        while True:
            try:
                await self.archive_old_events()
            except Exception as e:
                logger.error(f"❌ Archival job failed: {e}", exc_info=True)
            
            # Wait until next run
            await asyncio.sleep(self.config.ARCHIVE_INTERVAL_HOURS * 3600)
    
    async def archive_old_events(self):
        """
        Archive events older than ARCHIVE_AFTER_DAYS to S3.
        Deletes from ClickHouse after successful upload.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.config.ARCHIVE_AFTER_DAYS)
        logger.info(f"🗄️  Archiving events older than {cutoff_date.date()}")
        
        # Query events to archive
        query = f"""
        SELECT
            event_id,
            project_id,
            type,
            timestamp,
            sdk_name,
            sdk_version,
            body,
            context,
            queued_at,
            processed_at,
            queue_latency_ms,
            estimated_cost_usd
        FROM events
        WHERE toDate(timestamp) < toDate('{cutoff_date.strftime('%Y-%m-%d')}')
        ORDER BY timestamp
        LIMIT {self.config.BATCH_SIZE}
        """
        
        loop = asyncio.get_event_loop()
        events = await loop.run_in_executor(None, self._query_clickhouse, query)
        
        if not events:
            logger.info("✅ No events to archive")
            return
        
        logger.info(f"📦 Found {len(events)} events to archive")
        
        # Group events by month (for organized S3 structure)
        events_by_month = self._group_events_by_month(events)
        
        for month_key, month_events in events_by_month.items():
            await self._archive_month_batch(month_key, month_events)
        
        logger.info(f"✅ Archived {len(events)} events to S3")
    
    def _query_clickhouse(self, query: str) -> List[Dict[str, Any]]:
        """Execute ClickHouse query synchronously."""
        if not self.clickhouse.client:
            self.clickhouse._connect_sync()
        
        rows = self.clickhouse.client.execute(query, with_column_types=True)
        
        if not rows:
            return []
        
        # Parse results
        data, columns = rows[0], rows[1] if len(rows) > 1 else []
        
        if not columns:
            # No column metadata, return raw rows
            return [dict(enumerate(row)) for row in data]
        
        # Build dict from column names
        column_names = [col[0] for col in columns]
        return [dict(zip(column_names, row)) for row in data]
    
    def _group_events_by_month(
        self, events: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group events by YYYY-MM for organized S3 storage."""
        grouped = {}
        
        for event in events:
            timestamp = event.get("timestamp")
            if isinstance(timestamp, datetime):
                month_key = timestamp.strftime("%Y-%m")
            elif isinstance(timestamp, str):
                month_key = timestamp[:7]  # "2024-01-15" -> "2024-01"
            else:
                month_key = "unknown"
            
            if month_key not in grouped:
                grouped[month_key] = []
            
            grouped[month_key].append(event)
        
        return grouped
    
    async def _archive_month_batch(self, month_key: str, events: List[Dict[str, Any]]):
        """
        Archive a batch of events for a specific month.
        Uploads to S3 as Parquet and deletes from ClickHouse.
        """
        logger.info(f"📦 Archiving {len(events)} events for {month_key}")
        
        # Convert to Parquet
        parquet_buffer = self._convert_to_parquet(events)
        
        # Upload to S3
        s3_key = f"{self.config.S3_PREFIX}/{month_key}/events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._upload_to_s3,
            s3_key,
            parquet_buffer,
        )
        
        logger.info(f"✅ Uploaded to s3://{self.config.S3_BUCKET}/{s3_key}")
        
        # Delete from ClickHouse if configured
        if self.config.DELETE_AFTER_ARCHIVE:
            event_ids = [event["event_id"] for event in events]
            await self._delete_from_clickhouse(event_ids)
            logger.info(f"🗑️  Deleted {len(event_ids)} events from ClickHouse")
    
    def _convert_to_parquet(self, events: List[Dict[str, Any]]) -> bytes:
        """Convert events to Parquet format."""
        # Build PyArrow schema
        schema = pa.schema([
            ("event_id", pa.string()),
            ("project_id", pa.string()),
            ("type", pa.string()),
            ("timestamp", pa.timestamp("ms")),
            ("sdk_name", pa.string()),
            ("sdk_version", pa.string()),
            ("body", pa.string()),
            ("context", pa.string()),
            ("queued_at", pa.timestamp("ms")),
            ("processed_at", pa.timestamp("ms")),
            ("queue_latency_ms", pa.float32()),
            ("estimated_cost_usd", pa.float64()),
        ])
        
        # Convert to PyArrow Table
        arrays = []
        for field in schema:
            field_name = field.name
            
            if field.type == pa.timestamp("ms"):
                # Convert datetime/strings to timestamps
                values = []
                for event in events:
                    val = event.get(field_name)
                    if isinstance(val, datetime):
                        values.append(val)
                    elif isinstance(val, str):
                        try:
                            values.append(datetime.fromisoformat(val.replace("Z", "+00:00")))
                        except:
                            values.append(None)
                    else:
                        values.append(None)
                arrays.append(pa.array(values, type=field.type))
            else:
                # Other types
                values = [event.get(field_name) for event in events]
                arrays.append(pa.array(values, type=field.type))
        
        table = pa.Table.from_arrays(arrays, schema=schema)
        
        # Write to buffer
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)
        
        return buffer.getvalue()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _upload_to_s3(self, key: str, data: bytes):
        """Upload data to S3 with retries."""
        try:
            self.s3_client.put_object(
                Bucket=self.config.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType="application/octet-stream",
                StorageClass="STANDARD_IA",  # Infrequent Access for cost savings
            )
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise
    
    async def _delete_from_clickhouse(self, event_ids: List[str]):
        """Delete archived events from ClickHouse."""
        if not event_ids:
            return
        
        # ClickHouse DELETE requires ALTER TABLE permissions
        # Use lightweight DELETE mutation (available in ClickHouse 22.8+)
        ids_str = "', '".join(str(id) for id in event_ids)
        delete_query = f"DELETE FROM events WHERE event_id IN ('{ids_str}')"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._execute_clickhouse_mutation,
            delete_query,
        )
    
    def _execute_clickhouse_mutation(self, query: str):
        """Execute ClickHouse mutation (DELETE/UPDATE) synchronously."""
        if not self.clickhouse.client:
            self.clickhouse._connect_sync()
        
        self.clickhouse.client.execute(query)
    
    async def verify_archive(self, s3_key: str) -> bool:
        """
        Verify that an archived file exists and is readable.
        Useful for testing and data integrity checks.
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.s3_client.head_object,
                {"Bucket": self.config.S3_BUCKET, "Key": s3_key},
            )
            logger.info(f"✅ Archive verified: s3://{self.config.S3_BUCKET}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"❌ Archive verification failed: {e}")
            return False


# =============================================================================
# Archiver Singleton
# =============================================================================

_archiver: Optional[S3Archiver] = None


def get_archiver(clickhouse_client: ClickHouseClient) -> S3Archiver:
    """Get or create S3 archiver singleton."""
    global _archiver
    if _archiver is None:
        _archiver = S3Archiver(clickhouse_client)
    return _archiver

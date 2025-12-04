"""
ClickHouse Client Module.
Handles writing events to ClickHouse for analytics.
"""

import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from clickhouse_driver import Client
from clickhouse_driver.errors import NetworkError, ServerException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings

logger = logging.getLogger("lynex.processor.clickhouse")

# =============================================================================
# ClickHouse Client
# =============================================================================

class ClickHouseClient:
    """
    Async ClickHouse client using clickhouse-driver with connection pooling.
    """
    
    def __init__(self):
        self.host = settings.clickhouse_host
        self.port = settings.clickhouse_port
        self.user = settings.clickhouse_user
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self.client: Optional[Client] = None
        
        # Event buffer for batching
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100  # Flush after 100 events
        self._last_flush = datetime.utcnow()
    
    async def connect(self):
        """Initialize the ClickHouse client."""
        try:
            # Run connection in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect_sync)
            logger.info(f"✅ ClickHouse connection established: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((NetworkError, ServerException, OSError)),
        reraise=True
    )
    def _connect_sync(self):
        """Synchronous connection logic."""
        logger.info(f"Connecting to ClickHouse at {self.host}:{self.port}...")
        self.client = Client(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            connect_timeout=10,
            send_receive_timeout=30,
            sync_request_timeout=30,
        )
        # Test connection
        self.client.execute("SELECT 1")
        logger.info("✅ ClickHouse connection established")
    
    async def close(self):
        """Close the client and flush remaining events."""
        if self._buffer:
            await self.flush()
        
        if self.client:
            self.client.disconnect()
            logger.info("ClickHouse connection closed")
    
    async def query(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """Execute a query and return the result."""
        if not self.client:
            await self.connect()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._query_sync, sql, params)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, ServerException))
    )
    def _query_sync(self, sql: str, params: Dict[str, Any] = None):
        if not self.client:
            self._connect_sync()
        return self.client.execute(sql, params)
    
    async def insert_event(self, event: Dict[str, Any]):
        """
        Add an event to the buffer.
        Flushes automatically when buffer is full.
        """
        self._buffer.append(event)
        
        if len(self._buffer) >= self._buffer_size:
            await self.flush()
    
    async def insert_events(self, events: List[Dict[str, Any]]):
        """Add multiple events to the buffer."""
        self._buffer.extend(events)
        
        if len(self._buffer) >= self._buffer_size:
            await self.flush()
    
    async def flush(self):
        """Flush the event buffer to ClickHouse."""
        if not self._buffer:
            return
        
        if not self.client:
            await self.connect()
        
        events_to_insert = self._buffer.copy()
        self._buffer.clear()
        
        try:
            # Prepare rows for insertion
            rows = []
            for event in events_to_insert:
                row = {
                    "event_id": event.get("event_id", ""),
                    "project_id": event.get("project_id", ""),
                    "type": event.get("type", "custom"),
                    "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                    "sdk_name": event.get("sdk", {}).get("name", "unknown"),
                    "sdk_version": event.get("sdk", {}).get("version", "0.0.0"),
                    "body": json.dumps(event.get("body", {})),
                    "context": json.dumps(event.get("context", {})),
                    "queued_at": event.get("queued_at", datetime.utcnow().isoformat()),
                    "processed_at": event.get("processed_at", datetime.utcnow().isoformat()),
                    "queue_latency_ms": event.get("queue_latency_ms", 0),
                    "estimated_cost_usd": event.get("estimated_cost_usd", 0),
                }
                rows.append(row)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._insert_sync, rows)
            
            logger.info(f"✅ Flushed {len(events_to_insert)} events to ClickHouse")
            self._last_flush = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"❌ ClickHouse insert failed: {e}")
            # Put events back in buffer for retry
            self._buffer.extend(events_to_insert)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, ServerException))
    )
    def _insert_sync(self, rows: List[Dict[str, Any]]):
        if not self.client:
            self._connect_sync()
        
        self.client.execute(
            "INSERT INTO events (event_id, project_id, type, timestamp, sdk_name, sdk_version, body, context, queued_at, processed_at, queue_latency_ms, estimated_cost_usd) VALUES",
            rows
        )



# =============================================================================
# Singleton Instance
# =============================================================================

_clickhouse_client: Optional[ClickHouseClient] = None


async def get_clickhouse_client() -> ClickHouseClient:
    """Get or create ClickHouse client singleton."""
    global _clickhouse_client
    
    if _clickhouse_client is None:
        _clickhouse_client = ClickHouseClient()
        await _clickhouse_client.connect()
    
    return _clickhouse_client


async def close_clickhouse_client():
    """Close ClickHouse client."""
    global _clickhouse_client
    
    if _clickhouse_client:
        await _clickhouse_client.close()
        _clickhouse_client = None


# =============================================================================
# Convenience Functions
# =============================================================================

async def insert_event(event: Dict[str, Any]):
    """Insert a single event."""
    client = await get_clickhouse_client()
    await client.insert_event(event)


async def insert_events(events: List[Dict[str, Any]]):
    """Insert multiple events."""
    client = await get_clickhouse_client()
    await client.insert_events(events)


async def flush():
    """Flush pending events."""
    client = await get_clickhouse_client()
    await client.flush()


async def query(sql: str) -> str:
    """Execute a query."""
    client = await get_clickhouse_client()
    return await client.query(sql)

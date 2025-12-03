"""
ClickHouse Client Module.
Handles writing events to ClickHouse for analytics.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from config import settings

logger = logging.getLogger("sentryai.processor.clickhouse")

_use_mock_mode = False

# =============================================================================
# ClickHouse Client
# =============================================================================

class ClickHouseClient:
    """
    Async ClickHouse client using HTTP interface.
    
    Uses httpx for async HTTP requests to ClickHouse's HTTP interface,
    which is simpler than native protocol and works with all providers.
    """
    
    def __init__(self):
        self.base_url = f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
        self.user = settings.clickhouse_user
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self.client: Optional[httpx.AsyncClient] = None
        
        # Event buffer for batching
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100  # Flush after 100 events
        self._last_flush = datetime.utcnow()
    
    async def connect(self):
        """Initialize the HTTP client."""
        global _use_mock_mode
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(self.user, self.password) if self.password else None,
            timeout=30.0,
        )
        
        # Test connection
        try:
            result = await self.query("SELECT 1")
            logger.info(f"✅ ClickHouse connection established: {self.base_url}")
        except Exception as e:
            logger.warning(f"⚠️ ClickHouse not available: {e}")
            logger.info("📦 Using mock mode (events will be logged but not stored)")
            _use_mock_mode = True
    
    async def close(self):
        """Close the HTTP client and flush remaining events."""
        if self._buffer:
            await self.flush()
        
        if self.client:
            await self.client.aclose()
            logger.info("ClickHouse connection closed")
    
    async def query(self, sql: str, params: Dict[str, Any] = None) -> str:
        """Execute a query and return the result."""
        global _use_mock_mode
        
        if _use_mock_mode:
            return "1"
            
        if not self.client:
            await self.connect()
        
        query_params = {"database": self.database}
        if params:
            query_params.update(params)
        
        response = await self.client.post(
            "/",
            params=query_params,
            content=sql,
        )
        response.raise_for_status()
        return response.text
    
    async def insert_event(self, event: Dict[str, Any]):
        """
        Add an event to the buffer.
        Flushes automatically when buffer is full.
        """
        global _use_mock_mode
        
        if _use_mock_mode:
            logger.info(f"📦 [Mock] Would insert event: {event.get('event_id')}")
            return

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
            # Build INSERT statement with JSONEachRow format
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
                rows.append(json.dumps(row))
            
            data = "\n".join(rows)
            
            response = await self.client.post(
                "/",
                params={
                    "database": self.database,
                    "query": "INSERT INTO events FORMAT JSONEachRow",
                },
                content=data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            logger.info(f"✅ Flushed {len(events_to_insert)} events to ClickHouse")
            self._last_flush = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"❌ ClickHouse insert failed: {e}")
            # Put events back in buffer for retry
            self._buffer.extend(events_to_insert)
            raise


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

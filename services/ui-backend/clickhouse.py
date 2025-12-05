"""
ClickHouse Client for Query API.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from clickhouse_driver import Client
from clickhouse_driver.errors import NetworkError, ServerException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings

logger = logging.getLogger("watchllm.query.clickhouse")

class ClickHouseClient:
    """Async ClickHouse client for queries using clickhouse-driver."""
    
    def __init__(self):
        self.host = settings.clickhouse_host
        self.port = settings.clickhouse_port
        self.user = settings.clickhouse_user
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self.client: Optional[Client] = None
    
    async def connect(self):
        """Initialize ClickHouse client."""
        try:
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
        self.client.execute("SELECT 1")
        logger.info("✅ ClickHouse connection established")
    
    async def close(self):
        """Close the client."""
        if self.client:
            self.client.disconnect()
            logger.info("ClickHouse connection closed")
    
    async def query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as a list of dictionaries."""
        if not self.client:
            await self.connect()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._query_sync, sql, params)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, ServerException))
    )
    def _query_sync(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not self.client:
            self._connect_sync()
        
        result, columns = self.client.execute(sql, params, with_column_types=True)
        
        # Convert to list of dicts
        data = []
        for row in result:
            item = {}
            for i, col in enumerate(columns):
                item[col[0]] = row[i]
            data.append(item)
        
        return data

# =============================================================================
# Singleton Instance
# =============================================================================

_client: Optional[ClickHouseClient] = None

async def get_client() -> ClickHouseClient:
    """Get or create ClickHouse client singleton."""
    global _client
    if _client is None:
        _client = ClickHouseClient()
        await _client.connect()
    return _client

async def close_client():
    """Close ClickHouse client."""
    global _client
    if _client:
        await _client.close()
        _client = None


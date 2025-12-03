"""
ClickHouse Client for Query API.
"""

import json
import logging
from typing import Optional, Dict, Any, List

import httpx

from config import settings

logger = logging.getLogger("sentryai.query.clickhouse")


class ClickHouseClient:
    """Async ClickHouse client for queries."""
    
    def __init__(self):
        self.base_url = f"http://{settings.clickhouse_host}:{settings.clickhouse_port}"
        self.user = settings.clickhouse_user
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(self.user, self.password) if self.password else None,
            timeout=30.0,
        )
        
        try:
            await self.query("SELECT 1")
            logger.info(f"✅ ClickHouse connected: {self.base_url}")
        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
    
    async def query(self, sql: str, format: str = "JSON") -> Any:
        """Execute query and return result."""
        if not self.client:
            await self.connect()
        
        response = await self.client.post(
            "/",
            params={"database": self.database},
            content=f"{sql} FORMAT {format}",
        )
        response.raise_for_status()
        
        if format == "JSON":
            return response.json()
        return response.text


# Singleton
_client: Optional[ClickHouseClient] = None

async def get_client() -> ClickHouseClient:
    global _client
    if _client is None:
        _client = ClickHouseClient()
        await _client.connect()
    return _client

async def close_client():
    global _client
    if _client:
        await _client.close()
        _client = None

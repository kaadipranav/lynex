"""
ClickHouse Client for Query API.
Includes mock data fallback for local testing.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import random

import httpx

from config import settings

logger = logging.getLogger("lynex.query.clickhouse")


# =============================================================================
# Mock Data for Testing
# =============================================================================

_use_mock_data = False

def generate_mock_events(project_id: str, count: int = 50) -> List[Dict]:
    """Generate mock event data for testing."""
    event_types = ["log", "error", "span", "token_usage", "model_response"]
    models = ["gpt-4", "gpt-3.5-turbo", "claude-2", "claude-instant"]
    
    events = []
    base_time = datetime.utcnow()
    
    for i in range(count):
        event_type = random.choice(event_types)
        timestamp = base_time - timedelta(minutes=i * random.randint(1, 10))
        
        body = {"message": f"Mock event #{i}"}
        if event_type == "token_usage":
            body = {
                "model": random.choice(models),
                "prompt_tokens": random.randint(10, 500),
                "completion_tokens": random.randint(10, 1000),
            }
        elif event_type == "error":
            body = {
                "error": "MockError",
                "message": f"Something went wrong #{i}",
                "stack_trace": "at mock_function() line 42"
            }
        elif event_type == "model_response":
            body = {
                "model": random.choice(models),
                "latency_ms": random.randint(100, 3000),
                "status": "success"
            }
        
        events.append({
            "event_id": f"evt_{i:04d}_{random.randint(1000, 9999)}",
            "project_id": project_id,
            "type": event_type,
            "timestamp": timestamp.isoformat(),
            "sdk_name": "lynex-python",
            "sdk_version": "1.0.0",
            "body": json.dumps(body),
            "context": json.dumps({"environment": "development"}),
            "estimated_cost_usd": round(random.uniform(0.001, 0.1), 4),
            "queue_latency_ms": random.randint(5, 50),
        })
    
    return events


def generate_mock_stats(project_id: str) -> Dict:
    """Generate mock stats for testing."""
    return {
        "total_events": random.randint(1000, 50000),
        "events_24h": random.randint(100, 5000),
        "error_rate": round(random.uniform(0.5, 5.0), 2),
        "avg_latency_ms": random.randint(50, 500),
        "total_cost_usd": round(random.uniform(1, 100), 2),
        "total_tokens": random.randint(10000, 1000000),
    }


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
        global _use_mock_data
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(self.user, self.password) if self.password else None,
            timeout=30.0,
        )
        
        try:
            await self.query("SELECT 1", use_mock=False)
            logger.info(f"✅ ClickHouse connected: {self.base_url}")
        except Exception as e:
            logger.warning(f"⚠️ ClickHouse not available: {e}")
            logger.info("📦 Using mock data for testing")
            _use_mock_data = True
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
    
    async def query(self, sql: str, format: str = "JSON", use_mock: bool = True) -> Any:
        """Execute query and return result."""
        global _use_mock_data
        
        if _use_mock_data and use_mock:
            return self._mock_query(sql)
        
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
    
    def _mock_query(self, sql: str) -> Dict:
        """Return mock data based on query type."""
        sql_lower = sql.lower()
        
        # Handle count queries
        if "count()" in sql_lower:
            return {"data": [{"total": random.randint(100, 5000)}]}
        
        # Handle events queries
        if "from events" in sql_lower:
            # Extract project_id from query if possible
            project_id = "proj_demo"
            events = generate_mock_events(project_id, 50)
            return {"data": events}
        
        # Handle stats queries (time series)
        if "group by" in sql_lower and ("todate" in sql_lower or "tohour" in sql_lower):
            data = []
            for i in range(24):
                data.append({
                    "time": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "count": random.randint(10, 500),
                    "errors": random.randint(0, 20),
                })
            return {"data": data}
        
        # Default
        return {"data": []}


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


def is_using_mock() -> bool:
    """Check if using mock data."""
    return _use_mock_data

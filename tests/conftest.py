"""
Pytest configuration and fixtures for WatchLLM tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services"))


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# MongoDB Mocks
# =============================================================================

@pytest.fixture
def mock_mongodb():
    """Mock MongoDB client for unit tests."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    # Mock common collection methods
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.find = MagicMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    
    return mock_client


@pytest.fixture
def mock_subscription_data():
    """Sample subscription data for testing."""
    return {
        "user_id": "test-user-123",
        "project_id": "test-project-456",
        "tier": "PRO",
        "monthly_limit": 1000000,
        "usage": 500000,
        "period_start": "2025-12-01T00:00:00Z",
        "stripe_subscription_id": "sub_test123",
        "active": True,
    }


# =============================================================================
# ClickHouse Mocks
# =============================================================================

@pytest.fixture
def mock_clickhouse():
    """Mock ClickHouse client for unit tests."""
    mock_client = MagicMock()
    
    # Mock execute method
    mock_client.execute = MagicMock(return_value=[])
    
    return mock_client


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "event_id": "evt_test123",
        "project_id": "test-project-456",
        "type": "log",
        "timestamp": "2025-12-05T10:00:00Z",
        "sdk": {"name": "watchllm-python", "version": "0.1.0"},
        "body": {
            "level": "info",
            "message": "Test log message",
        },
        "metadata": {"env": "test"},
    }


@pytest.fixture
def sample_token_usage_event():
    """Sample token usage event for testing."""
    return {
        "event_id": "evt_token123",
        "project_id": "test-project-456",
        "type": "token_usage",
        "timestamp": "2025-12-05T10:00:00Z",
        "sdk": {"name": "watchllm-python", "version": "0.1.0"},
        "body": {
            "model": "gpt-4",
            "inputTokens": 100,
            "outputTokens": 50,
            "totalTokens": 150,
        },
    }


# =============================================================================
# Redis Mocks
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for unit tests."""
    mock_client = AsyncMock()
    
    # Mock common Redis methods
    mock_client.xadd = AsyncMock(return_value=b"1234567890-0")
    mock_client.xread = AsyncMock(return_value=[])
    mock_client.xack = AsyncMock()
    mock_client.incr = AsyncMock(return_value=1)
    mock_client.expire = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock()
    
    return mock_client


# =============================================================================
# API Test Client Fixtures
# =============================================================================

@pytest.fixture
def test_api_key():
    """Test API key for authentication."""
    return "test_key_123456789"


@pytest.fixture
def mock_api_key_data():
    """Mock APIKeyData for authentication."""
    from collections import namedtuple
    APIKeyData = namedtuple("APIKeyData", ["user_id", "project_id", "tier"])
    return APIKeyData(
        user_id="test-user-123",
        project_id="test-project-456",
        tier="PRO",
    )


# =============================================================================
# Pricing Test Data
# =============================================================================

@pytest.fixture
def pricing_test_cases():
    """Test cases for pricing calculator."""
    return [
        {
            "model": "gpt-4",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_cost": 0.06,  # (1000/1M * 30) + (500/1M * 60)
        },
        {
            "model": "gpt-4o-mini",
            "input_tokens": 1000000,
            "output_tokens": 1000000,
            "expected_cost": 0.75,  # (1M/1M * 0.15) + (1M/1M * 0.60)
        },
        {
            "model": "claude-3-opus-20240229",  # Versioned model name
            "input_tokens": 100000,
            "output_tokens": 50000,
            "expected_cost": 5.25,  # (100K/1M * 15) + (50K/1M * 75)
        },
    ]


# =============================================================================
# Alert Test Data
# =============================================================================

@pytest.fixture
def sample_alert_rule():
    """Sample alert rule for testing."""
    return {
        "rule_id": "rule_test123",
        "project_id": "test-project-456",
        "name": "High Error Rate",
        "event_type": "error",
        "condition": "count",
        "threshold": 10,
        "window_seconds": 300,
        "channels": ["email"],
        "enabled": True,
    }

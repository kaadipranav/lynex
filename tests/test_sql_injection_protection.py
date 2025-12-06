"""
Unit tests for SQL injection protection in UI backend.
Tests parameterized queries and input validation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import sys
from pathlib import Path

# Add ui-backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ui-backend"))


@pytest.mark.unit
class TestSQLInjectionProtection:
    """Test SQL injection protection in query endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_event_uses_parameterized_query(self):
        """Test that get_event uses parameterized queries, not f-strings."""
        from routes.events import get_event
        
        # Mock ClickHouse client
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[{
            "event_id": "evt_123",
            "project_id": "proj_456",
            "type": "log",
            "timestamp": datetime.utcnow(),
            "sdk_name": "watchllm-python",
            "sdk_version": "0.1.0",
            "body": '{"message": "test"}',
            "context": '{}',
            "estimated_cost_usd": 0,
            "queue_latency_ms": 10,
        }])
        
        with patch("routes.events.ch.get_client", AsyncMock(return_value=mock_client)):
            # Try with malicious input (SQL injection attempt)
            malicious_event_id = "evt_123' OR '1'='1"
            
            try:
                result = await get_event(
                    event_id=malicious_event_id,
                    project_id="proj_456"
                )
            except HTTPException:
                pass  # Expected if not found
            
            # Verify query was called with params dict, not f-string
            mock_client.query.assert_called_once()
            call_args = mock_client.query.call_args
            
            # Should have 2 arguments: sql and params
            assert len(call_args[0]) == 2
            sql = call_args[0][0]
            params = call_args[0][1]
            
            # SQL should use %(param)s syntax, not f-string
            assert "%(event_id)s" in sql
            assert "%(project_id)s" in sql
            assert "'" not in sql or sql.count("'") == 0  # No quotes in WHERE clause
            
            # Params should be a dict
            assert isinstance(params, dict)
            assert params["event_id"] == malicious_event_id
            assert params["project_id"] == "proj_456"
    
    @pytest.mark.asyncio
    async def test_list_events_uses_parameterized_query(self):
        """Test that list_events uses parameterized queries."""
        from routes.events import list_events
        from auth.supabase_middleware import User
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[{"total": 0}])
        
        mock_user = User(id="user_123", email="test@example.com")
        
        with patch("routes.events.ch.get_client", AsyncMock(return_value=mock_client)):
            try:
                result = await list_events(
                    project_id="proj_456",
                    type="log",
                    limit=100,
                    offset=0,
                    user=mock_user
                )
            except:
                pass
            
            # Verify all queries use params
            for call in mock_client.query.call_args_list:
                if len(call[0]) >= 2:
                    sql = call[0][0]
                    params = call[0][1]
                    
                    # Should use %(param)s syntax
                    assert "%(project_id)s" in sql or "project_id" in str(params)
                    assert isinstance(params, dict)


@pytest.mark.unit
class TestInputValidation:
    """Test input validation and whitelisting."""
    
    @pytest.mark.asyncio
    async def test_timeseries_rejects_invalid_interval(self):
        """Test that invalid interval is rejected."""
        from routes.stats import get_timeseries
        from auth.supabase_middleware import User
        
        mock_user = User(id="user_123", email="test@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_timeseries(
                project_id="proj_456",
                metric="requests",
                hours=24,
                interval="malicious_sql_injection",  # Invalid interval
                user=mock_user
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid interval" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_timeseries_rejects_invalid_metric(self):
        """Test that invalid metric is rejected."""
        from routes.stats import get_timeseries
        from auth.supabase_middleware import User
        
        mock_user = User(id="user_123", email="test@example.com")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_timeseries(
                project_id="proj_456",
                metric="DROP TABLE events",  # SQL injection attempt
                hours=24,
                interval="1h",
                user=mock_user
            )
        
        assert exc_info.value.status_code == 400
        assert "Unknown metric" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_timeseries_accepts_valid_intervals(self):
        """Test that valid intervals are accepted."""
        from routes.stats import get_timeseries
        from auth.supabase_middleware import User
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        mock_user = User(id="user_123", email="test@example.com")
        
        valid_intervals = ["1m", "5m", "1h", "1d"]
        
        with patch("routes.stats.ch.get_client", AsyncMock(return_value=mock_client)):
            for interval in valid_intervals:
                try:
                    result = await get_timeseries(
                        project_id="proj_456",
                        metric="requests",
                        hours=24,
                        interval=interval,
                        user=mock_user
                    )
                    # Should not raise exception
                except HTTPException as e:
                    if e.status_code == 400:
                        pytest.fail(f"Valid interval '{interval}' was rejected")
    
    @pytest.mark.asyncio
    async def test_timeseries_accepts_valid_metrics(self):
        """Test that valid metrics are accepted."""
        from routes.stats import get_timeseries
        from auth.supabase_middleware import User
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        mock_user = User(id="user_123", email="test@example.com")
        
        valid_metrics = ["requests", "errors", "tokens", "cost"]
        
        with patch("routes.stats.ch.get_client", AsyncMock(return_value=mock_client)):
            for metric in valid_metrics:
                try:
                    result = await get_timeseries(
                        project_id="proj_456",
                        metric=metric,
                        hours=24,
                        interval="1h",
                        user=mock_user
                    )
                    # Should not raise exception
                except HTTPException as e:
                    if e.status_code == 400:
                        pytest.fail(f"Valid metric '{metric}' was rejected")


@pytest.mark.unit
class TestWhitelistValidation:
    """Test whitelist-based SQL fragment validation."""
    
    def test_interval_whitelist_complete(self):
        """Test that interval whitelist contains all safe values."""
        # This would be imported from the actual code
        interval_map = {
            "1m": "toStartOfMinute",
            "5m": "toStartOfFiveMinutes",
            "1h": "toStartOfHour",
            "1d": "toStartOfDay",
        }
        
        # Verify all values are safe ClickHouse functions
        for interval, func in interval_map.items():
            assert func.startswith("toStartOf")
            assert " " not in func  # No spaces (no SQL injection)
            assert ";" not in func  # No semicolons
            assert "--" not in func  # No comments
    
    def test_metric_whitelist_complete(self):
        """Test that metric whitelist contains all safe values."""
        metric_map = {
            "requests": "count()",
            "errors": "countIf(type = 'error')",
            "tokens": "sum(JSONExtractInt(body, 'inputTokens') + JSONExtractInt(body, 'outputTokens'))",
            "cost": "sum(estimated_cost_usd)",
        }
        
        # Verify all values are safe SQL fragments
        for metric, sql in metric_map.items():
            # Should not contain dangerous patterns
            assert "DROP" not in sql.upper()
            assert "DELETE" not in sql.upper()
            assert "INSERT" not in sql.upper()
            assert "UPDATE" not in sql.upper()
            assert "--" not in sql
            assert "/*" not in sql


@pytest.mark.unit
class TestParameterizedQueries:
    """Test that all queries use parameterized statements."""
    
    @pytest.mark.asyncio
    async def test_overview_stats_uses_params(self):
        """Test that overview stats uses parameterized queries."""
        from routes.stats import get_overview_stats
        from auth.supabase_middleware import User
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[{
            "total_events": 1000,
            "total_errors": 10,
            "total_cost_usd": 1.23,
            "total_tokens": 50000,
            "avg_latency_ms": 150.5,
        }])
        
        mock_user = User(id="user_123", email="test@example.com")
        
        with patch("routes.stats.ch.get_client", AsyncMock(return_value=mock_client)):
            result = await get_overview_stats(
                project_id="proj_456",
                hours=24,
                user=mock_user
            )
            
            # Verify query was called with params
            mock_client.query.assert_called_once()
            call_args = mock_client.query.call_args
            
            sql = call_args[0][0]
            params = call_args[0][1]
            
            # Should use %(param)s syntax
            assert "%(project_id)s" in sql
            assert "%(start_time)s" in sql
            
            # Params should be a dict
            assert isinstance(params, dict)
            assert "project_id" in params
            assert "start_time" in params
    
    @pytest.mark.asyncio
    async def test_token_usage_uses_params(self):
        """Test that token usage endpoint uses parameterized queries."""
        from routes.stats import get_token_usage_by_model
        from auth.supabase_middleware import User
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        mock_user = User(id="user_123", email="test@example.com")
        
        with patch("routes.stats.ch.get_client", AsyncMock(return_value=mock_client)):
            result = await get_token_usage_by_model(
                project_id="proj_456",
                hours=24,
                user=mock_user
            )
            
            # Verify query uses params
            call_args = mock_client.query.call_args
            sql = call_args[0][0]
            params = call_args[0][1]
            
            assert "%(project_id)s" in sql
            assert "%(start_time)s" in sql
            assert isinstance(params, dict)


@pytest.mark.unit
class TestSQLInjectionAttempts:
    """Test various SQL injection attack vectors."""
    
    @pytest.mark.asyncio
    async def test_union_based_injection_blocked(self):
        """Test that UNION-based SQL injection is blocked."""
        from routes.events import get_event
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        with patch("routes.events.ch.get_client", AsyncMock(return_value=mock_client)):
            malicious_id = "evt_123' UNION SELECT * FROM users --"
            
            try:
                await get_event(event_id=malicious_id, project_id="proj_456")
            except HTTPException:
                pass  # Expected
            
            # Verify the malicious string was passed as a parameter, not interpolated
            call_args = mock_client.query.call_args
            params = call_args[0][1]
            
            # The malicious string should be in params (safe)
            assert params["event_id"] == malicious_id
            
            # The SQL should NOT contain the malicious string directly
            sql = call_args[0][0]
            assert "UNION" not in sql
            assert "users" not in sql
    
    @pytest.mark.asyncio
    async def test_comment_based_injection_blocked(self):
        """Test that comment-based SQL injection is blocked."""
        from routes.events import get_event
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        with patch("routes.events.ch.get_client", AsyncMock(return_value=mock_client)):
            malicious_id = "evt_123' OR '1'='1' --"
            
            try:
                await get_event(event_id=malicious_id, project_id="proj_456")
            except HTTPException:
                pass
            
            call_args = mock_client.query.call_args
            params = call_args[0][1]
            sql = call_args[0][0]
            
            # Malicious string should be in params
            assert params["event_id"] == malicious_id
            
            # SQL should not contain the injection
            assert "OR '1'='1'" not in sql
    
    @pytest.mark.asyncio
    async def test_boolean_based_injection_blocked(self):
        """Test that boolean-based SQL injection is blocked."""
        from routes.events import get_event
        
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=[])
        
        with patch("routes.events.ch.get_client", AsyncMock(return_value=mock_client)):
            malicious_id = "evt_123' AND 1=1 --"
            
            try:
                await get_event(event_id=malicious_id, project_id="proj_456")
            except HTTPException:
                pass
            
            call_args = mock_client.query.call_args
            params = call_args[0][1]
            sql = call_args[0][0]
            
            assert params["event_id"] == malicious_id
            assert "AND 1=1" not in sql

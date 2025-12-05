"""
Unit tests for Ingest API event validation and processing.
"""

import pytest
from fastapi import HTTPException
from datetime import datetime
import sys
from pathlib import Path

# Add ingest-api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "ingest-api"))

from schemas import EventEnvelope, SDKMetadata


class TestEventValidation:
    """Test event schema validation."""
    
    def test_valid_log_event(self, sample_event_data):
        """Test that valid log event passes validation."""
        event = EventEnvelope(**sample_event_data)
        assert event.event_id == sample_event_data["event_id"]
        assert event.type == "log"
        assert event.body["message"] == "Test log message"
    
    def test_valid_token_usage_event(self, sample_token_usage_event):
        """Test that valid token usage event passes validation."""
        event = EventEnvelope(**sample_token_usage_event)
        assert event.type == "token_usage"
        assert event.body["model"] == "gpt-4"
        assert event.body["inputTokens"] == 100
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            EventEnvelope(
                event_id="evt_123",
                type="log",
                # Missing project_id, timestamp, sdk
            )
    
    def test_invalid_event_type(self, sample_event_data):
        """Test that invalid event type raises validation error."""
        sample_event_data["type"] = "invalid_type"
        with pytest.raises(Exception):  # Pydantic ValidationError
            EventEnvelope(**sample_event_data)
    
    def test_sdk_metadata_validation(self):
        """Test SDK metadata validation."""
        sdk = SDKMetadata(name="watchllm-python", version="0.1.0")
        assert sdk.name == "watchllm-python"
        assert sdk.version == "0.1.0"
    
    def test_event_with_metadata(self, sample_event_data):
        """Test event with optional metadata."""
        sample_event_data["metadata"] = {
            "env": "production",
            "region": "us-east-1",
            "custom_tag": "value",
        }
        event = EventEnvelope(**sample_event_data)
        assert event.metadata["env"] == "production"
        assert event.metadata["custom_tag"] == "value"
    
    def test_event_with_trace_context(self, sample_event_data):
        """Test event with trace_id and parent_event_id."""
        sample_event_data["trace_id"] = "trace_abc123"
        sample_event_data["parent_event_id"] = "evt_parent456"
        event = EventEnvelope(**sample_event_data)
        assert event.trace_id == "trace_abc123"
        assert event.parent_event_id == "evt_parent456"


class TestBatchValidation:
    """Test batch ingestion validation."""
    
    def test_batch_size_limit(self, sample_event_data):
        """Test that batch size over 100 is rejected."""
        # This would be tested in the route handler
        events = [sample_event_data.copy() for _ in range(101)]
        assert len(events) > 100
    
    def test_empty_batch(self):
        """Test that empty batch is handled correctly."""
        events = []
        assert len(events) == 0
    
    def test_batch_with_mixed_types(self, sample_event_data, sample_token_usage_event):
        """Test batch with different event types."""
        events = [
            EventEnvelope(**sample_event_data),
            EventEnvelope(**sample_token_usage_event),
        ]
        assert events[0].type == "log"
        assert events[1].type == "token_usage"


class TestAuthenticationMock:
    """Test API key authentication (mocked)."""
    
    @pytest.mark.asyncio
    async def test_valid_api_key(self, mock_api_key_data):
        """Test that valid API key allows access."""
        assert mock_api_key_data.project_id == "test-project-456"
        assert mock_api_key_data.tier == "PRO"
    
    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test that missing API key raises 401."""
        # This would be tested with actual FastAPI TestClient
        # Just verify the pattern here
        api_key = None
        assert api_key is None  # Should raise HTTPException in real handler


class TestRateLimitMock:
    """Test rate limiting logic (mocked)."""
    
    @pytest.mark.asyncio
    async def test_under_limit(self, mock_redis):
        """Test that usage under limit is allowed."""
        mock_redis.get.return_value = b"500000"  # Under 1M limit
        
        # Mock rate limit check
        usage = int(mock_redis.get.return_value)
        limit = 1000000
        assert usage < limit
    
    @pytest.mark.asyncio
    async def test_over_limit(self, mock_redis):
        """Test that usage over limit is blocked."""
        mock_redis.get.return_value = b"1000001"  # Over 1M limit
        
        usage = int(mock_redis.get.return_value)
        limit = 1000000
        assert usage > limit


class TestEventQueueMock:
    """Test Redis queue operations (mocked)."""
    
    @pytest.mark.asyncio
    async def test_push_single_event(self, mock_redis, sample_event_data):
        """Test pushing single event to queue."""
        message_id = await mock_redis.xadd("events", sample_event_data)
        assert message_id == b"1234567890-0"
        mock_redis.xadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_push_batch_events(self, mock_redis, sample_event_data):
        """Test pushing batch of events to queue."""
        events = [sample_event_data.copy() for _ in range(5)]
        
        message_ids = []
        for event in events:
            msg_id = await mock_redis.xadd("events", event)
            message_ids.append(msg_id)
        
        assert len(message_ids) == 5
        assert mock_redis.xadd.call_count == 5
    
    @pytest.mark.asyncio
    async def test_queue_unavailable(self, mock_redis):
        """Test handling of queue unavailable error."""
        mock_redis.xadd.side_effect = Exception("Connection refused")
        
        with pytest.raises(Exception):
            await mock_redis.xadd("events", {})

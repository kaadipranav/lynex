"""
End-to-End Integration Test for WatchLLM.
Tests the full flow: SDK -> Ingest API -> Queue -> Processor -> ClickHouse -> UI Backend.
"""

import pytest
import asyncio
import httpx
from datetime import datetime
import uuid


class TestE2EEventFlow:
    """
    End-to-end test for event ingestion flow.
    
    Prerequisites:
    - All services running (docker-compose up)
    - Test API key configured
    - Clean database state
    """
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_ingest_and_retrieve_event(self):
        """
        Test complete flow:
        1. Send event to Ingest API
        2. Wait for processing
        3. Query UI Backend to verify event stored
        """
        # Configuration
        ingest_url = "http://localhost:8001/api/v1/events"
        ui_backend_url = "http://localhost:8003/api/v1/events"
        api_key = "test_api_key_123"  # Replace with actual test key
        project_id = "test-project-e2e"
        
        # Create test event
        event_id = f"evt_test_{uuid.uuid4().hex[:8]}"
        event = {
            "event_id": event_id,
            "project_id": project_id,
            "type": "log",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sdk": {
                "name": "watchllm-test",
                "version": "1.0.0"
            },
            "body": {
                "level": "info",
                "message": "E2E test event"
            },
            "metadata": {
                "test": "e2e",
                "run_id": str(uuid.uuid4())
            }
        }
        
        # Step 1: Send event to Ingest API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ingest_url,
                json=event,
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"
            assert data["event_id"] == event_id
            print(f"✅ Event queued: {event_id}")
        
        # Step 2: Wait for processing (processor polls every 1s)
        await asyncio.sleep(3)
        print("⏳ Waited for processing...")
        
        # Step 3: Query UI Backend to verify event
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ui_backend_url,
                params={"project_id": project_id, "limit": 10},
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Find our event
            events = data.get("events", [])
            found = any(e["event_id"] == event_id for e in events)
            
            assert found, f"Event {event_id} not found in UI Backend response"
            print(f"✅ Event retrieved: {event_id}")
            
            # Verify event data
            test_event = next(e for e in events if e["event_id"] == event_id)
            assert test_event["type"] == "log"
            assert test_event["body"]["message"] == "E2E test event"
            assert test_event["metadata"]["test"] == "e2e"
            print("✅ Event data verified")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_batch_ingest_and_retrieve(self):
        """Test batch ingestion flow."""
        ingest_url = "http://localhost:8001/api/v1/events/batch"
        ui_backend_url = "http://localhost:8003/api/v1/events"
        api_key = "test_api_key_123"
        project_id = "test-project-e2e"
        
        # Create batch of 10 events
        batch_id = uuid.uuid4().hex[:8]
        events = []
        for i in range(10):
            event = {
                "event_id": f"evt_batch_{batch_id}_{i}",
                "project_id": project_id,
                "type": "log",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "sdk": {
                    "name": "watchllm-test",
                    "version": "1.0.0"
                },
                "body": {
                    "level": "info",
                    "message": f"Batch test event {i}"
                },
                "metadata": {
                    "batch_id": batch_id,
                    "index": i
                }
            }
            events.append(event)
        
        # Send batch
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ingest_url,
                json=events,
                headers={"X-API-Key": api_key},
                timeout=10.0
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "queued"
            assert data["count"] == 10
            print(f"✅ Batch of 10 events queued")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Verify all events stored
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ui_backend_url,
                params={"project_id": project_id, "limit": 50},
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Find all batch events
            batch_events = [
                e for e in data.get("events", [])
                if e.get("metadata", {}).get("batch_id") == batch_id
            ]
            
            assert len(batch_events) == 10, f"Expected 10 events, found {len(batch_events)}"
            print(f"✅ All 10 batch events retrieved")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_token_usage_cost_calculation(self):
        """Test that token usage events get cost enrichment."""
        ingest_url = "http://localhost:8001/api/v1/events"
        ui_backend_url = "http://localhost:8003/api/v1/events"
        api_key = "test_api_key_123"
        project_id = "test-project-e2e"
        
        event_id = f"evt_cost_{uuid.uuid4().hex[:8]}"
        event = {
            "event_id": event_id,
            "project_id": project_id,
            "type": "token_usage",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sdk": {
                "name": "watchllm-test",
                "version": "1.0.0"
            },
            "body": {
                "model": "gpt-4",
                "inputTokens": 1000,
                "outputTokens": 500,
                "totalTokens": 1500
            }
        }
        
        # Send event
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ingest_url,
                json=event,
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            assert response.status_code == 202
        
        # Wait for processing and enrichment
        await asyncio.sleep(3)
        
        # Retrieve and verify cost was calculated
        async with httpx.AsyncClient() as client:
            response = await client.get(
                ui_backend_url,
                params={"project_id": project_id, "limit": 10},
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            
            assert response.status_code == 200
            events = response.json().get("events", [])
            
            test_event = next((e for e in events if e["event_id"] == event_id), None)
            assert test_event is not None
            
            # Verify cost was enriched
            assert "estimated_cost_usd" in test_event
            assert test_event["estimated_cost_usd"] > 0
            print(f"✅ Cost calculated: ${test_event['estimated_cost_usd']:.6f}")
            
            # Verify cost breakdown
            if "cost_breakdown" in test_event:
                breakdown = test_event["cost_breakdown"]
                assert "input_cost" in breakdown
                assert "output_cost" in breakdown
                print(f"   Input: ${breakdown['input_cost']:.6f}")
                print(f"   Output: ${breakdown['output_cost']:.6f}")


class TestE2ETracing:
    """Test distributed tracing E2E flow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_trace_hierarchy(self):
        """Test creating and retrieving hierarchical trace."""
        ingest_url = "http://localhost:8001/api/v1/events"
        traces_url = "http://localhost:8003/api/v1/traces"
        api_key = "test_api_key_123"
        project_id = "test-project-e2e"
        
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"
        
        # Create parent span
        parent_id = f"evt_parent_{uuid.uuid4().hex[:8]}"
        parent_event = {
            "event_id": parent_id,
            "project_id": project_id,
            "type": "span",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sdk": {"name": "watchllm-test", "version": "1.0.0"},
            "body": {
                "name": "parent_operation",
                "status": "success"
            }
        }
        
        # Create child span
        child_id = f"evt_child_{uuid.uuid4().hex[:8]}"
        child_event = {
            "event_id": child_id,
            "project_id": project_id,
            "type": "span",
            "trace_id": trace_id,
            "parent_event_id": parent_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sdk": {"name": "watchllm-test", "version": "1.0.0"},
            "body": {
                "name": "child_operation",
                "status": "success"
            }
        }
        
        # Send both events
        async with httpx.AsyncClient() as client:
            await client.post(
                ingest_url,
                json=parent_event,
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            await client.post(
                ingest_url,
                json=child_event,
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Retrieve trace
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{traces_url}/{trace_id}",
                params={"project_id": project_id},
                headers={"X-API-Key": api_key},
                timeout=5.0
            )
            
            assert response.status_code == 200
            trace_data = response.json()
            
            # Verify hierarchy was built
            assert trace_data["trace_id"] == trace_id
            assert "spans" in trace_data
            
            # Find parent and child in hierarchy
            spans = trace_data["spans"]
            parent_span = next((s for s in spans if s["event_id"] == parent_id), None)
            
            assert parent_span is not None
            assert "children" in parent_span
            assert len(parent_span["children"]) == 1
            assert parent_span["children"][0]["event_id"] == child_id
            
            print(f"✅ Trace hierarchy verified: {trace_id}")
            print(f"   Parent: {parent_id}")
            print(f"   Child: {child_id}")

# Local Testing Guide for Lynex

Complete guide to test the entire MVP locally without Docker (or with Docker).

## Table of Contents
1. [Quick Start (No Docker)](#quick-start-no-docker) - **Recommended for first-time testing**
2. [Full Stack with Docker](#full-stack-with-docker)
3. [Testing the SDKs](#testing-the-sdks)
4. [Troubleshooting](#troubleshooting)

---

## Quick Start (No Docker)

This is the **fastest way** to test locally. You'll run services directly with Python.

### Step 1: Install Dependencies (Already Done ✅)

```powershell
# Services dependencies are already installed
# Verify:
python -c "import motor, redis, pydantic; print('✅ All core dependencies available')"
```

### Step 2: Start Services in Separate Terminals

Open **4 PowerShell windows**:

#### **Terminal 1: Ingest API (Port 8000)**
```powershell
cd d:\Lynex
python run_ingest.py
```
Should see: `INFO: Uvicorn running on http://0.0.0.0:8000`

#### **Terminal 2: UI Backend (Port 8001)**
```powershell
cd d:\Lynex
python run_ui_backend.py
```
Should see: `INFO: Uvicorn running on http://0.0.0.0:8001`

#### **Terminal 3: Processor Worker**
```powershell
cd d:\Lynex
python run_processor.py
```
Should see: `INFO: Starting processor...`

#### **Terminal 4: Test Client** (After services start)
```powershell
cd d:\Lynex
python test_sdk.py
```

### Step 3: Verify Connection (Give it 10 seconds)

You should see output like:
```
🚀 Sending test events...
✅ Log sent
✅ Error sent
✅ Usage sent
⏳ Waiting for flush...
🎉 Done!
```

**Note:** You might see MongoDB connection warnings - **that's OK** for this test since we're using in-memory storage for demo.

---

## Full Stack with Docker

Use this when you want persistent data and production-like environment.

### Prerequisites

- Docker Desktop **must be running** (check Windows system tray)
- Available ports: 8000, 8001, 8002, 6379, 27017, 8123

### Step 1: Start Infrastructure

```powershell
cd d:\Lynex
docker-compose up --build
```

**Wait for output:** All services should show "healthy" or "Application startup complete"

**Services that will start:**
- ClickHouse (Analytics) - http://localhost:8123
- MongoDB (Data) - localhost:27017
- Redis (Queue) - localhost:6379
- Ingest API - http://localhost:8000
- UI Backend - http://localhost:8001
- Billing Service - http://localhost:8002
- Processor - Background worker

### Step 2: Test Events

In a new terminal:
```powershell
cd d:\Lynex
python test_sdk.py
```

### Step 3: View Dashboard

```powershell
cd d:\Lynex\web
npm install
npm run dev
```

Access: http://localhost:5173

---

## Testing the SDKs

### Python SDK

#### Test 1: Basic Initialization
```python
from watchllm import WatchLLM

client = WatchLLM(
    api_key="sk_test_demo1234567890abcdefghijklmno",
    project_id="proj_demo",
    host="http://localhost:8000"
)

# Test if it initializes without error
print("✅ Python SDK initialized successfully")
```

#### Test 2: Send Events
```powershell
# This will test the full event pipeline
cd d:\Lynex
python test_sdk.py
```

#### Test 3: Custom Events
```python
from watchllm import WatchLLM
import time

client = WatchLLM(
    api_key="sk_test_demo1234567890abcdefghijklmno",
    host="http://localhost:8000"
)

# Test different event types
client.capture_log("Test message", level="info")
client.capture_log("Warning test", level="warning")

# Test LLM usage tracking
client.capture_llm_usage(
    model="gpt-4",
    input_tokens=100,
    output_tokens=200,
    cost=0.003
)

print("✅ All events sent!")
time.sleep(2)  # Wait for flush
```

### JavaScript SDK

#### Test 1: Build SDK
```powershell
cd d:\Lynex\libs\sdk-js
npm run build
```
Should complete with no errors.

#### Test 2: SDK Types
```powershell
cd d:\Lynex\libs\sdk-js
npm test
```

---

## Testing Endpoints

### Health Check
```powershell
curl http://localhost:8000/health
```
Expected response: `{"status": "ok"}`

### Ingest Event (Manual Test)
```powershell
$headers = @{
    "X-API-Key" = "sk_test_demo1234567890abcdefghijklmno"
    "Content-Type" = "application/json"
}

$body = @{
    event_type = "llm_completion"
    model = "gpt-4"
    tokens_input = 100
    tokens_output = 200
    latency_ms = 1500
    cost_usd = 0.003
    status = "success"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/v1/events" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

### Get Metrics
```powershell
curl http://localhost:8000/metrics
```

---

## Testing Flow (End-to-End)

### Scenario 1: Basic Event Flow
1. ✅ Start Ingest API (`python run_ingest.py`)
2. ✅ Run SDK test (`python test_sdk.py`)
3. ✅ Check for successful event transmission
4. ✅ Verify no errors in API logs

### Scenario 2: Full Pipeline
1. ✅ Start all services (Ingest API, UI Backend, Processor)
2. ✅ Send events via SDK (`python test_sdk.py`)
3. ✅ Monitor processor logs (should show event processing)
4. ✅ Query metrics endpoint (should show event counts)

### Scenario 3: Dashboard Integration
1. ✅ Start all backend services
2. ✅ Start frontend (`cd web && npm run dev`)
3. ✅ Access http://localhost:5173
4. ✅ Send events and verify they appear

---

## Verification Checklist

After starting services, verify each:

- [ ] **Ingest API responds** (run `curl http://localhost:8000/health`)
- [ ] **UI Backend responds** (run `curl http://localhost:8001/health`)
- [ ] **SDK initializes** (run `python -c "from watchllm import WatchLLM; print('✅')"`)
- [ ] **Events send** (run `python test_sdk.py`)
- [ ] **Metrics available** (run `curl http://localhost:8000/metrics`)
- [ ] **Frontend loads** (visit http://localhost:5173 in browser)

---

## Troubleshooting

### "Connection refused" on Event Send

**Problem:** SDK can't connect to API

**Solutions:**
```powershell
# 1. Verify API is running
curl http://localhost:8000/health

# 2. Check if port is in use
netstat -ano | findstr :8000

# 3. Restart API service
python run_ingest.py
```

### "ModuleNotFoundError: No module named 'motor'"

**Problem:** Dependencies not installed

**Solution:**
```powershell
cd d:\Lynex\services\ingest-api
pip install -r requirements.txt
```

### "MongoDB connection refused"

**Problem:** MongoDB not running (can ignore for basic testing)

**Solution:**
```powershell
# Use Docker:
docker-compose up -d mongodb

# OR just continue - the SDK still works for demo
```

### "Port already in use"

**Problem:** Port 8000 or 8001 already in use

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill it (replace PID)
taskkill /PID <PID> /F

# OR change the port in run_ingest.py
```

### Services Won't Start

**Problem:** Syntax or import errors

**Solution:**
```powershell
# Check for syntax errors
python -m py_compile services/ingest-api/main.py

# Verify imports
python -c "from services.ingest_api.main import app; print('✅')"
```

---

## Quick Test Scripts

### Test 1: SDK Functionality
Save as `test_quick.py`:
```python
from watchllm import WatchLLM
import time

print("Testing Lynex SDK...")

client = WatchLLM(
    api_key="sk_test_demo1234567890abcdefghijklmno",
    host="http://localhost:8000"
)

print("✅ SDK initialized")

# Send event
client.capture_log("Test event", level="info")
print("✅ Event sent")

time.sleep(2)
print("🎉 Test complete!")
```

Run: `python test_quick.py`

### Test 2: API Health
Save as `test_health.py`:
```python
import requests

endpoints = [
    ("Ingest API", "http://localhost:8000/health"),
    ("UI Backend", "http://localhost:8001/health"),
]

for name, url in endpoints:
    try:
        r = requests.get(url, timeout=5)
        print(f"✅ {name}: {r.status_code}")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

Run: `python test_health.py`

### Test 3: Event Flow
Save as `test_event_flow.py`:
```python
import requests
import json

api_key = "sk_test_demo1234567890abcdefghijklmno"
url = "http://localhost:8000/api/v1/events"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

event = {
    "event_type": "test_event",
    "timestamp": "2025-12-05T19:00:00Z",
    "metadata": {"test": True}
}

try:
    r = requests.post(url, json=event, headers=headers, timeout=10)
    print(f"✅ Event sent: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"❌ Failed: {e}")
```

Run: `python test_event_flow.py`

---

## Recommended Testing Order

1. **Start with No-Docker approach** (faster feedback)
2. **Test SDK first** (simplest)
3. **Test individual endpoints** (isolate issues)
4. **Test full pipeline** (all services)
5. **Add Docker** (when you need persistence)

---

## Performance Expectations

**With no database persistence:**
- Event ingestion: <50ms
- API response time: <100ms
- SDK initialization: <100ms

**With Docker + databases:**
- Event ingestion: 50-200ms
- API response time: 100-500ms
- Requires ~30s startup time

---

## Next Steps

After successful local testing:

1. ✅ **Try the Dashboard** - http://localhost:5173
2. ✅ **Generate API Key** - Settings page
3. ✅ **Create custom events** - Test different event types
4. ✅ **Check metrics** - http://localhost:8000/metrics
5. ✅ **Deploy to production** - Use docker-compose.yml

---

**Happy testing! 🚀**

# AI Agent Implementation Guide: Datadog, Sentry & DigitalOcean

**Purpose:** This guide provides step-by-step instructions for an AI agent to implement Datadog, Sentry, and DigitalOcean deployment.  
**Execution Mode:** Sequential - Complete each task in order before proceeding to the next.  
**Validation:** Each task includes verification steps to confirm success.

---

## Pre-Implementation Checklist

Before starting, verify:
- [ ] Current working directory is `d:\Lynex`
- [ ] All services can run locally (test with existing run scripts)
- [ ] `.env` file exists in project root
- [ ] Python 3.11+ is installed
- [ ] Node.js 18+ is installed (for frontend)

---

## TASK 1: Sentry Integration (Error Tracking)

**Objective:** Add Sentry SDK to all Python services for error tracking  
**Time Estimate:** 30 minutes  
**Dependencies:** None

### 1.1: Install Sentry SDK Dependencies

**Action:** Add Sentry SDK to all service requirements files.

**Files to Modify:**
1. `services/ingest-api/requirements.txt`
2. `services/processor/requirements.txt`
3. `services/ui-backend/requirements.txt`

**Changes:**
Add this line to each file:
```
sentry-sdk[fastapi]>=1.40.0
```

**Verification:**
```bash
# Run from project root
pip install -r services/ingest-api/requirements.txt
pip install -r services/processor/requirements.txt
pip install -r services/ui-backend/requirements.txt
```

Expected: No errors, packages install successfully.

---

### 1.2: Add Environment Configuration

**Action:** Add `env` field to config files for environment tracking.

**File:** `services/ingest-api/config.py`

**Location:** After line 86 (after `debug` field), before `sentry_dsn` field

**Add:**
```python
    env: str = Field(
        default="development",
        description="Environment: development, staging, or production"
    )
```

**Repeat for:**
- `services/processor/config.py` (same location pattern)
- `services/ui-backend/config.py` (same location pattern)

**Verification:**
```bash
python -c "from services.ingest_api.config import settings; print(settings.env)"
```

Expected: Prints "development" (or value from .env)

---

### 1.3: Initialize Sentry in Ingest API

**Action:** Add Sentry initialization to the Ingest API service.

**File:** `services/ingest-api/main.py`

**Location:** After line 10 (after existing imports)

**Add these imports:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
```

**Location:** After line 26 (after logger setup, before lifespan function)

**Add this code:**
```python
# =============================================================================
# Sentry Initialization
# =============================================================================

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=1.0 if settings.debug else 0.1,
        profiles_sample_rate=1.0 if settings.debug else 0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        # Additional metadata
        release=f"lynex-ingest@1.0.0",
        server_name="ingest-api",
    )
    logger.info("✅ Sentry initialized for error tracking")
else:
    logger.warning("⚠️  Sentry DSN not configured - error tracking disabled")
```

**Verification:**
```bash
cd services/ingest-api
python main.py
```

Expected: See log message about Sentry initialization status.

---

### 1.4: Initialize Sentry in Processor

**Action:** Add Sentry initialization to the Processor worker.

**File:** `services/processor/main.py`

**Location:** After imports section (around line 15)

**Add import:**
```python
import sentry_sdk
```

**Location:** Inside `main()` function, after logger setup (around line 47)

**Add:**
```python
    # Initialize Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.env,
            traces_sample_rate=1.0 if settings.debug else 0.1,
            release=f"lynex-processor@1.0.0",
            server_name="processor",
        )
        logger.info("✅ Sentry initialized for error tracking")
    else:
        logger.warning("⚠️  Sentry DSN not configured")
```

**Verification:**
```bash
cd services/processor
python main.py
```

Expected: See Sentry initialization log message.

---

### 1.5: Initialize Sentry in UI Backend

**Action:** Add Sentry initialization to the UI Backend service.

**File:** `services/ui-backend/main.py`

**Follow same pattern as Task 1.3:**
1. Add imports after line 10
2. Add initialization after logger setup (around line 26)
3. Use `release=f"lynex-ui-backend@1.0.0"` and `server_name="ui-backend"`

**Verification:**
```bash
cd services/ui-backend
python main.py
```

Expected: See Sentry initialization log message.

---

### 1.6: Add Sentry Test Endpoint

**Action:** Add a test endpoint to verify Sentry is capturing errors.

**File:** `services/ingest-api/main.py`

**Location:** After the root endpoint (around line 133), before the router include

**Add:**
```python
# Sentry test endpoint (only in debug mode)
if settings.debug:
    @app.get("/sentry-test", tags=["Health"])
    async def sentry_test():
        """Test Sentry error tracking - only available in debug mode"""
        logger.info("Triggering test error for Sentry")
        raise Exception("🧪 This is a test error for Sentry! If you see this in Sentry dashboard, integration is working.")
```

**Verification:**
1. Start ingest API: `python services/ingest-api/main.py`
2. Visit: `http://localhost:8000/sentry-test`
3. Expected: 500 error in browser
4. Check Sentry dashboard (after setting up DSN) for the error

---

### 1.7: Update Environment File Template

**Action:** Add Sentry configuration to environment template.

**File:** `.env.example`

**Location:** Add to the "Monitoring" section (create if doesn't exist)

**Add:**
```bash
# =============================================================================
# Monitoring & Observability
# =============================================================================

# Sentry Error Tracking (Get DSN from https://sentry.io)
SENTRY_DSN=
ENV=development  # Options: development, staging, production

# Datadog APM (Get API key from https://app.datadoghq.com)
DATADOG_API_KEY=
DD_SERVICE=lynex
DD_ENV=development
DD_VERSION=1.0.0
```

**Verification:**
Check that `.env.example` has the new section.

---

### 1.8: Verification Checklist for Sentry

**Manual Steps:**
1. Sign up at https://sentry.io (use GitHub Student Pack)
2. Create new project: "Lynex"
3. Copy the DSN (format: `https://xxx@xxx.ingest.sentry.io/xxx`)
4. Add to `.env`: `SENTRY_DSN=your-dsn-here`
5. Restart all services
6. Visit `http://localhost:8000/sentry-test`
7. Check Sentry dashboard for the error

**Expected Results:**
- ✅ All services start without errors
- ✅ Log messages show "Sentry initialized"
- ✅ Test error appears in Sentry dashboard
- ✅ Error includes stack trace and context

**If verification fails:**
- Check SENTRY_DSN is correctly set in .env
- Verify sentry-sdk is installed: `pip list | grep sentry`
- Check logs for initialization errors

---

## TASK 2: Datadog Integration (APM & Metrics)

**Objective:** Add Datadog APM for performance monitoring  
**Time Estimate:** 45 minutes  
**Dependencies:** Task 1 complete

### 2.1: Install Datadog SDK

**Action:** Add Datadog tracing library to all service requirements.

**Files to Modify:**
1. `services/ingest-api/requirements.txt`
2. `services/processor/requirements.txt`
3. `services/ui-backend/requirements.txt`

**Add:**
```
ddtrace>=2.0.0
```

**Verification:**
```bash
pip install -r services/ingest-api/requirements.txt
pip install -r services/processor/requirements.txt
pip install -r services/ui-backend/requirements.txt
```

Expected: ddtrace installs successfully.

---

### 2.2: Add Datadog Configuration to Settings

**Action:** Add Datadog-specific configuration fields.

**File:** `services/ingest-api/config.py`

**Location:** After `sentry_dsn` field (around line 92)

**Add:**
```python
    # ----- Datadog APM -----
    datadog_enabled: bool = Field(
        default=False,
        description="Enable Datadog APM tracing"
    )
    dd_service: str = Field(
        default="lynex-ingest-api",
        description="Datadog service name"
    )
    dd_env: str = Field(
        default="development",
        description="Datadog environment"
    )
    dd_version: str = Field(
        default="1.0.0",
        description="Application version for Datadog"
    )
```

**Repeat for:**
- `services/processor/config.py` (use `dd_service="lynex-processor"`)
- `services/ui-backend/config.py` (use `dd_service="lynex-ui-backend"`)

**Verification:**
```bash
python -c "from services.ingest_api.config import settings; print(settings.dd_service)"
```

Expected: Prints the service name.

---

### 2.3: Initialize Datadog in Ingest API

**Action:** Add Datadog APM initialization.

**File:** `services/ingest-api/main.py`

**Location:** After Sentry imports (around line 13)

**Add import:**
```python
from ddtrace import tracer, patch_all
import os
```

**Location:** After Sentry initialization block (around line 50)

**Add:**
```python
# =============================================================================
# Datadog APM Initialization
# =============================================================================

if settings.datadog_enabled:
    # Set Datadog environment variables
    os.environ["DD_SERVICE"] = settings.dd_service
    os.environ["DD_ENV"] = settings.dd_env
    os.environ["DD_VERSION"] = settings.dd_version
    os.environ["DD_LOGS_INJECTION"] = "true"
    os.environ["DD_TRACE_SAMPLE_RATE"] = "1.0" if settings.debug else "0.1"
    
    # Auto-instrument FastAPI, Redis, HTTP clients
    patch_all()
    
    logger.info(f"✅ Datadog APM initialized (service: {settings.dd_service})")
else:
    logger.info("ℹ️  Datadog APM disabled")
```

**Verification:**
```bash
# Set in .env: DATADOG_ENABLED=true
python services/ingest-api/main.py
```

Expected: See "Datadog APM initialized" in logs.

---

### 2.4: Add Custom Datadog Tracing to Events Endpoint

**Action:** Add custom tracing spans to track event ingestion performance.

**File:** `services/ingest-api/routes/events.py`

**Location:** After imports (around line 10)

**Add:**
```python
from ddtrace import tracer
```

**Location:** Inside the `ingest_event` function, wrap the main logic

**Find the existing function and modify it:**
```python
@router.post("/events", status_code=202)
async def ingest_event(
    event: Event,
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Ingest an event into the queue."""
    
    # Start custom trace span
    with tracer.trace("event.ingest", service="lynex-ingest-api") as span:
        # Add custom tags for filtering in Datadog
        span.set_tag("event.type", event.type)
        span.set_tag("project.id", event.project_id)
        span.set_tag("sdk.name", event.sdk.name if event.sdk else "unknown")
        
        # Existing logic here...
        # (keep all the existing code, just wrap it in the span)
        
        # Your existing code continues...
```

**Note:** Only wrap the business logic, don't modify the actual implementation.

**Verification:**
After Datadog is fully set up, traces will appear in Datadog APM dashboard.

---

### 2.5: Initialize Datadog in Processor

**Action:** Add Datadog to the processor worker.

**File:** `services/processor/main.py`

**Location:** After imports

**Add:**
```python
from ddtrace import patch_all
import os
```

**Location:** In `main()` function, after Sentry initialization

**Add:**
```python
    # Initialize Datadog APM
    if settings.datadog_enabled:
        os.environ["DD_SERVICE"] = settings.dd_service
        os.environ["DD_ENV"] = settings.dd_env
        os.environ["DD_VERSION"] = settings.dd_version
        patch_all()
        logger.info(f"✅ Datadog APM initialized (service: {settings.dd_service})")
```

**Verification:**
```bash
DATADOG_ENABLED=true python services/processor/main.py
```

Expected: See Datadog initialization message.

---

### 2.6: Initialize Datadog in UI Backend

**Action:** Add Datadog to UI Backend service.

**File:** `services/ui-backend/main.py`

**Follow same pattern as Task 2.3:**
1. Add imports
2. Add initialization after Sentry block
3. Use service name from config

**Verification:**
Same as Task 2.5.

---

### 2.7: Update Environment Files

**Action:** Add Datadog configuration to .env files.

**File:** `.env` (create if doesn't exist)

**Add:**
```bash
# Datadog APM
DATADOG_ENABLED=false  # Set to true when ready to use
DD_SERVICE=lynex
DD_ENV=development
DD_VERSION=1.0.0
```

**File:** `.env.example`

**Verify the Datadog section was added in Task 1.7.**

---

### 2.8: Verification Checklist for Datadog

**Manual Steps (for later, when deploying):**
1. Sign up at https://www.datadoghq.com/students/
2. Get API key from https://app.datadoghq.com/organization-settings/api-keys
3. Install Datadog Agent (on production server):
   ```bash
   DD_API_KEY=your-key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"
   ```
4. Set `DATADOG_ENABLED=true` in production .env
5. Restart services

**Expected Results:**
- ✅ Services start with Datadog enabled
- ✅ Traces appear in Datadog APM dashboard
- ✅ Custom tags visible on traces
- ✅ Performance metrics collected

**Note:** Datadog requires the agent to be running. For local development, keep `DATADOG_ENABLED=false`.

---

## TASK 3: Docker Containerization

**Objective:** Create Docker containers for all services  
**Time Estimate:** 2 hours  
**Dependencies:** Tasks 1 & 2 complete

### 3.1: Create Dockerfile for Ingest API

**Action:** Create a production-ready Dockerfile.

**File:** `services/ingest-api/Dockerfile` (create new file)

**Content:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Verification:**
```bash
cd services/ingest-api
docker build -t lynex-ingest-api .
docker run -p 8000:8000 --env-file ../../.env lynex-ingest-api
```

Expected: Container builds and runs successfully.

---

### 3.2: Create Dockerfile for Processor

**Action:** Create Dockerfile for the processor worker.

**File:** `services/processor/Dockerfile` (create new file)

**Content:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check (check if process is running)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD pgrep -f "python.*main.py" || exit 1

CMD ["python", "main.py"]
```

**Verification:**
```bash
cd services/processor
docker build -t lynex-processor .
```

Expected: Builds successfully.

---

### 3.3: Create Dockerfile for UI Backend

**Action:** Create Dockerfile for UI Backend service.

**File:** `services/ui-backend/Dockerfile` (create new file)

**Content:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health', timeout=2)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
```

**Verification:**
```bash
cd services/ui-backend
docker build -t lynex-ui-backend .
```

Expected: Builds successfully.

---

### 3.4: Create Dockerfile for Frontend

**Action:** Create multi-stage Dockerfile for React frontend.

**File:** `web/Dockerfile` (create new file)

**Content:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Verification:**
```bash
cd web
docker build -t lynex-web .
```

Expected: Builds successfully (may take a few minutes).

---

### 3.5: Create Nginx Configuration for Frontend

**Action:** Create nginx config for serving the React app.

**File:** `web/nginx.conf` (create new file)

**Content:**
```nginx
server {
    listen 80;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy (optional - if you want to proxy backend through nginx)
    location /api/ {
        proxy_pass http://ui-backend:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Verification:**
Check file exists and syntax is correct.

---

### 3.6: Create Docker Compose File

**Action:** Create docker-compose.yml for local development and testing.

**File:** `docker-compose.yml` (create in project root)

**Content:**
```yaml
version: '3.8'

services:
  # Redis Queue
  redis:
    image: redis:7-alpine
    container_name: lynex-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

  # ClickHouse Database
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: lynex-clickhouse
    ports:
      - "8123:8123"
      - "9000:9000"
    volumes:
      - clickhouse-data:/var/lib/clickhouse
      - ./infra/clickhouse/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro
    environment:
      CLICKHOUSE_DB: lynex
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD:-}
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Ingest API
  ingest-api:
    build:
      context: ./services/ingest-api
      dockerfile: Dockerfile
    container_name: lynex-ingest-api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - CLICKHOUSE_HOST=clickhouse
      - CLICKHOUSE_PORT=8123
      - CLICKHOUSE_USER=default
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-}
      - SENTRY_DSN=${SENTRY_DSN:-}
      - ENV=${ENV:-development}
      - DATADOG_ENABLED=${DATADOG_ENABLED:-false}
      - DD_SERVICE=lynex-ingest-api
      - DD_ENV=${ENV:-development}
      - DD_AGENT_HOST=datadog-agent
    depends_on:
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
    restart: unless-stopped

  # Processor Worker
  processor:
    build:
      context: ./services/processor
      dockerfile: Dockerfile
    container_name: lynex-processor
    environment:
      - REDIS_URL=redis://redis:6379
      - CLICKHOUSE_HOST=clickhouse
      - CLICKHOUSE_PORT=8123
      - CLICKHOUSE_USER=default
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-}
      - SENTRY_DSN=${SENTRY_DSN:-}
      - ENV=${ENV:-development}
      - DATADOG_ENABLED=${DATADOG_ENABLED:-false}
      - DD_SERVICE=lynex-processor
      - DD_ENV=${ENV:-development}
      - DD_AGENT_HOST=datadog-agent
    depends_on:
      - redis
      - clickhouse
    restart: unless-stopped

  # UI Backend (Query API)
  ui-backend:
    build:
      context: ./services/ui-backend
      dockerfile: Dockerfile
    container_name: lynex-ui-backend
    ports:
      - "8001:8001"
    environment:
      - CLICKHOUSE_HOST=clickhouse
      - CLICKHOUSE_PORT=8123
      - CLICKHOUSE_USER=default
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-}
      - SENTRY_DSN=${SENTRY_DSN:-}
      - ENV=${ENV:-development}
      - DATADOG_ENABLED=${DATADOG_ENABLED:-false}
      - DD_SERVICE=lynex-ui-backend
      - DD_ENV=${ENV:-development}
      - DD_AGENT_HOST=datadog-agent
    depends_on:
      - clickhouse
    restart: unless-stopped

  # Frontend (React App)
  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    container_name: lynex-web
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8001
    depends_on:
      - ui-backend
    restart: unless-stopped

  # Datadog Agent (Optional - for production monitoring)
  datadog-agent:
    image: gcr.io/datadoghq/agent:latest
    container_name: datadog-agent
    environment:
      - DD_API_KEY=${DATADOG_API_KEY:-}
      - DD_SITE=datadoghq.com
      - DD_LOGS_ENABLED=true
      - DD_LOGS_CONFIG_CONTAINER_COLLECT_ALL=true
      - DD_CONTAINER_EXCLUDE="name:datadog-agent"
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
    ports:
      - "8126:8126"  # APM
    profiles:
      - monitoring  # Only start with: docker-compose --profile monitoring up

volumes:
  redis-data:
  clickhouse-data:
```

**Verification:**
```bash
# Test building all services
docker-compose build

# Test running all services
docker-compose up -d

# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Expected: All services build and run successfully.

---

### 3.7: Create .dockerignore Files

**Action:** Create .dockerignore to optimize Docker builds.

**File:** `services/ingest-api/.dockerignore`

**Content:**
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.env
.env.*
.git
.gitignore
.vscode
.idea
*.md
tests
.pytest_cache
```

**Repeat for:**
- `services/processor/.dockerignore` (same content)
- `services/ui-backend/.dockerignore` (same content)

**File:** `web/.dockerignore`

**Content:**
```
node_modules
dist
build
.git
.gitignore
.env
.env.*
*.md
.vscode
.idea
coverage
.cache
```

**Verification:**
Check files exist in correct locations.

---

### 3.8: Verification Checklist for Docker

**Commands to run:**
```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:3000

# View logs
docker-compose logs ingest-api
docker-compose logs processor
docker-compose logs ui-backend

# Stop services
docker-compose down
```

**Expected Results:**
- ✅ All images build without errors
- ✅ All services start successfully
- ✅ Health checks pass
- ✅ Frontend loads in browser
- ✅ No errors in logs

**If verification fails:**
- Check Docker is installed: `docker --version`
- Check Docker Compose is installed: `docker-compose --version`
- Review logs: `docker-compose logs [service-name]`
- Check .env file has required variables

---

## TASK 4: DigitalOcean Deployment Preparation

**Objective:** Prepare deployment scripts and documentation  
**Time Estimate:** 1 hour  
**Dependencies:** Task 3 complete

### 4.1: Create Deployment Documentation

**Action:** Create deployment guide for DigitalOcean.

**File:** `docs/DEPLOYMENT.md` (create new file)

**Content:**
```markdown
# Deployment Guide - DigitalOcean

## Prerequisites

- DigitalOcean account with $200 student credit
- GitHub repository with code
- Domain name (lynex.dev)
- Sentry account with DSN
- Datadog account with API key (optional)

## Option 1: DigitalOcean App Platform (Recommended)

### Advantages
- Automatic scaling
- Built-in SSL
- Easy rollbacks
- Managed databases available
- Zero-downtime deployments

### Steps

1. **Connect GitHub Repository**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Select "GitHub" as source
   - Authorize DigitalOcean
   - Select your repository

2. **Configure Services**
   
   **Ingest API:**
   - Type: Web Service
   - Source Directory: `/services/ingest-api`
   - Build Command: (auto-detected)
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port 8000`
   - HTTP Port: 8000
   - Instance Size: Basic ($12/month)
   
   **UI Backend:**
   - Type: Web Service
   - Source Directory: `/services/ui-backend`
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port 8001`
   - HTTP Port: 8001
   - Instance Size: Basic ($12/month)
   
   **Processor:**
   - Type: Worker
   - Source Directory: `/services/processor`
   - Run Command: `python main.py`
   - Instance Size: Basic ($12/month)
   
   **Frontend:**
   - Type: Static Site
   - Source Directory: `/web`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Add Managed Databases**
   - Add Redis (Managed Database) - $15/month
   - Add PostgreSQL for metadata (optional) - $15/month
   - For ClickHouse: Use Aiven or self-hosted droplet

4. **Configure Environment Variables**
   ```
   REDIS_URL=${redis.DATABASE_URL}
   CLICKHOUSE_HOST=your-clickhouse-host
   CLICKHOUSE_PASSWORD=your-password
   SENTRY_DSN=your-sentry-dsn
   ENV=production
   DATADOG_ENABLED=true
   DATADOG_API_KEY=your-datadog-key
   ```

5. **Deploy**
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)
   - App Platform will provide URLs

6. **Configure Custom Domain**
   - Go to Settings → Domains
   - Add `api.lynex.dev` → Ingest API
   - Add `app.lynex.dev` → Frontend
   - Update DNS records at your domain registrar

## Option 2: DigitalOcean Droplet (More Control)

### Advantages
- Full control
- Lower cost ($12/month for all services)
- Can run ClickHouse locally

### Steps

1. **Create Droplet**
   - Go to https://cloud.digitalocean.com/droplets
   - Create Droplet
   - Choose: Ubuntu 22.04 LTS
   - Size: Basic - $24/month (4GB RAM, 2 vCPUs)
   - Add SSH key
   - Create

2. **SSH into Droplet**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

4. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

5. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/lynex.git
   cd lynex
   ```

6. **Create Production .env**
   ```bash
   nano .env
   ```
   
   Add:
   ```
   REDIS_URL=redis://localhost:6379
   CLICKHOUSE_HOST=localhost
   CLICKHOUSE_PASSWORD=your-secure-password
   SENTRY_DSN=your-sentry-dsn
   ENV=production
   DATADOG_ENABLED=true
   DATADOG_API_KEY=your-datadog-key
   ```

7. **Start Services**
   ```bash
   docker-compose up -d
   ```

8. **Install Nginx for Reverse Proxy**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

9. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/lynex
   ```
   
   Add configuration (see nginx config below)

10. **Enable Site**
    ```bash
    sudo ln -s /etc/nginx/sites-available/lynex /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. **Get SSL Certificate**
    ```bash
    sudo certbot --nginx -d api.lynex.dev -d app.lynex.dev
    ```

12. **Install Datadog Agent**
    ```bash
    DD_API_KEY=your-key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"
    ```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/lynex

# API Backend
server {
    listen 80;
    server_name api.lynex.dev;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name app.lynex.dev;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Frontend Deployment to Vercel (Recommended)

1. **Sign up at Vercel**
   - Go to https://vercel.com
   - Sign up with GitHub

2. **Import Project**
   - Click "New Project"
   - Import your GitHub repository
   - Root Directory: `web/`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Environment Variables**
   ```
   VITE_API_URL=https://api.lynex.dev
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build (2-3 minutes)

5. **Custom Domain**
   - Go to Settings → Domains
   - Add `app.lynex.dev`
   - Update DNS records

## Cost Estimate

### App Platform
- 3 Web Services: $36/month
- 1 Worker: $12/month
- Managed Redis: $15/month
- **Total: ~$63/month** (covered by $200 credit for 3+ months)

### Droplet + Vercel
- 1 Droplet (4GB): $24/month
- Vercel: $0 (free tier)
- **Total: $24/month** (covered by $200 credit for 8+ months)

## Monitoring Setup

After deployment:

1. **Sentry**
   - Verify errors are being tracked
   - Set up alerts for critical errors

2. **Datadog**
   - Check APM dashboard for traces
   - Set up monitors for:
     - High error rate (>5%)
     - High latency (>1s p95)
     - Low throughput (<10 req/min)
   - Create dashboard with key metrics

3. **Uptime Monitoring**
   - Use UptimeRobot (free) or Datadog Synthetics
   - Monitor: api.lynex.dev/health
   - Alert on downtime

## Rollback Procedure

### App Platform
- Go to app settings
- Click "Rollback" to previous deployment

### Droplet
```bash
cd lynex
git checkout previous-commit
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Services won't start
- Check logs: `docker-compose logs [service]`
- Verify environment variables
- Check database connections

### High memory usage
- Reduce worker count
- Enable swap: `sudo fallocate -l 2G /swapfile`

### SSL certificate issues
- Renew: `sudo certbot renew`
- Check nginx config: `sudo nginx -t`
```

**Verification:**
Check file exists and is readable.

---

### 4.2: Create GitHub Actions Workflow

**Action:** Create CI/CD pipeline for automated deployments.

**File:** `.github/workflows/deploy.yml` (create new file)

**Content:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r services/ingest-api/requirements.txt
          pip install pytest
      
      - name: Run tests
        run: |
          # Add your test commands here
          echo "Tests would run here"

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service: [ingest-api, processor, ui-backend]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./services/${{ matrix.service }}
          push: true
          tags: ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}:latest

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./web
```

**Verification:**
Check file exists in `.github/workflows/` directory.

---

### 4.3: Create Production Environment Template

**Action:** Create a template for production environment variables.

**File:** `.env.production.example` (create in project root)

**Content:**
```bash
# =============================================================================
# PRODUCTION ENVIRONMENT VARIABLES
# =============================================================================
# Copy this file to .env.production and fill in the values

# ----- Queue -----
QUEUE_MODE=redis
REDIS_URL=redis://your-redis-host:6379
# Or for Upstash:
# REDIS_REST_URL=https://your-region.upstash.io
# REDIS_REST_TOKEN=your-token

# ----- Database -----
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-secure-password
CLICKHOUSE_DATABASE=lynex

# ----- API Server -----
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# ----- Environment -----
ENV=production

# ----- Monitoring -----
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
DATADOG_ENABLED=true
DATADOG_API_KEY=your-datadog-api-key
DD_SERVICE=lynex
DD_ENV=production
DD_VERSION=1.0.0

# ----- Security -----
# Add any API keys, secrets, JWT secrets here
```

**Verification:**
Check file exists.

---

### 4.4: Verification Checklist for Deployment Prep

**Files Created:**
- [ ] `docs/DEPLOYMENT.md`
- [ ] `.github/workflows/deploy.yml`
- [ ] `.env.production.example`

**Docker Verification:**
- [ ] All Dockerfiles exist
- [ ] docker-compose.yml exists
- [ ] Can build all images: `docker-compose build`
- [ ] Can run locally: `docker-compose up`

**Ready for Deployment:**
- [ ] Code is in GitHub repository
- [ ] Sentry is configured
- [ ] Datadog account created (optional)
- [ ] DigitalOcean account ready with $200 credit
- [ ] Domain name acquired (lynex.dev)

---

## FINAL VERIFICATION

### Complete System Test

Run these commands to verify everything is working:

```bash
# 1. Build all Docker images
docker-compose build

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be ready
sleep 30

# 4. Test Ingest API
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{
    "event_id": "test-123",
    "project_id": "test-project",
    "type": "log",
    "timestamp": "2025-12-04T12:00:00Z",
    "sdk": {"name": "test", "version": "1.0"},
    "body": {"message": "Test event"}
  }'

# 5. Test UI Backend
curl http://localhost:8001/health

# 6. Test Frontend
curl http://localhost:3000

# 7. Check Sentry (if configured)
curl http://localhost:8000/sentry-test

# 8. View logs
docker-compose logs -f

# 9. Stop services
docker-compose down
```

### Expected Results

- ✅ All services build without errors
- ✅ All services start successfully
- ✅ Health checks return 200 OK
- ✅ Event ingestion returns 202 Accepted
- ✅ Frontend loads in browser
- ✅ Sentry captures test error (if DSN configured)
- ✅ No critical errors in logs

---

## Deployment Checklist

Before deploying to production:

### Code Quality
- [ ] All services run locally without errors
- [ ] Docker containers build successfully
- [ ] docker-compose up works end-to-end
- [ ] No hardcoded secrets in code
- [ ] .env.example is up to date

### Monitoring
- [ ] Sentry DSN configured and tested
- [ ] Datadog account created (optional for now)
- [ ] Health check endpoints working

### Infrastructure
- [ ] DigitalOcean account with $200 credit
- [ ] Domain name (lynex.dev) configured
- [ ] SSL certificates plan (Vercel auto-SSL or Let's Encrypt)

### Documentation
- [ ] DEPLOYMENT.md is complete
- [ ] README.md updated with deployment info
- [ ] Environment variables documented

### Security
- [ ] All secrets in environment variables
- [ ] No API keys in code
- [ ] CORS configured properly
- [ ] Rate limiting considered

---

## Next Steps for AI Agent

After completing all tasks:

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "feat: add Sentry, Datadog, and Docker support"
   git push origin main
   ```

2. **Create deployment branch:**
   ```bash
   git checkout -b deploy/production
   git push origin deploy/production
   ```

3. **Manual steps required (human):**
   - Sign up for Sentry and get DSN
   - Sign up for Datadog and get API key
   - Create DigitalOcean account
   - Configure DNS for lynex.dev
   - Deploy using chosen method (App Platform or Droplet)

4. **Post-deployment:**
   - Verify all services are running
   - Check Sentry for errors
   - Check Datadog for metrics
   - Set up monitoring alerts
   - Test end-to-end functionality

---

## Troubleshooting Guide

### Common Issues

**Docker build fails:**
- Check Docker is installed: `docker --version`
- Check disk space: `df -h`
- Clear Docker cache: `docker system prune -a`

**Services won't start:**
- Check logs: `docker-compose logs [service-name]`
- Verify .env file exists and has correct values
- Check port conflicts: `netstat -tulpn | grep :8000`

**Sentry not receiving events:**
- Verify SENTRY_DSN is set correctly
- Check sentry-sdk is installed: `pip list | grep sentry`
- Test with /sentry-test endpoint
- Check Sentry project settings

**Datadog not showing metrics:**
- Verify DATADOG_ENABLED=true
- Check Datadog agent is running (in production)
- Verify API key is correct
- Check ddtrace is installed: `pip list | grep ddtrace`

**Frontend won't build:**
- Check Node.js version: `node --version` (should be 18+)
- Clear node_modules: `rm -rf node_modules && npm install`
- Check for TypeScript errors: `npm run build`

---

## Success Criteria

This implementation is complete when:

- ✅ All services have Sentry integration
- ✅ All services have Datadog APM support
- ✅ All services can run in Docker containers
- ✅ docker-compose.yml works end-to-end
- ✅ Deployment documentation is complete
- ✅ CI/CD pipeline is configured
- ✅ All verification tests pass

---

*This guide is designed for AI agents to follow step-by-step. Each task is atomic and includes verification steps.*

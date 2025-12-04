# MVP Task Breakdown — Lynex

> **Goal:** Ship a working MVP that can ingest AI events, store them, and display them on a dashboard.
> **Timeline:** 2-3 weeks (working solo with AI assistance).
> **Philosophy:** Each task is atomic. Complete one before moving to the next. Commit after each task.

---

## Phase 1: Foundation (Days 1-3)

### Task 1: Repo Setup ✅ COMPLETED
**Status:** Done
**Files Created:**
- `/services/ingest-api/`
- `/services/processor/`
- `/services/ui-backend/`
- `/services/billing/`
- `/libs/sdk-python/`
- `/libs/sdk-js/`
- `/web/`
- `/infra/`
- `/tests/`
- `/.github/workflows/`
- `/.gitignore`
- `/README.md`

---

### Task 2: Configuration System ✅ COMPLETED
**Status:** Done
**Files Created:**
- `/.env.example` — Template for all environment variables
- `/services/ingest-api/config.py` — Pydantic settings loader
- `/services/ingest-api/requirements.txt` — Python dependencies

**Your Action Required:**
1. Copy `.env.example` to `.env`
2. Sign up at [Upstash](https://upstash.com) and get Redis URL
3. (Optional for now) Sign up at [Aiven](https://aiven.io) for ClickHouse

---

### Task 3: Ingest API — Core Endpoint 🔲 NEXT
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/services/ingest-api/main.py` — FastAPI application
- `/services/ingest-api/schemas.py` — Pydantic models for events
- `/services/ingest-api/routes/events.py` — Event ingestion endpoint

**Detailed Requirements:**
1. **Endpoint:** `POST /api/v1/events`
2. **Request Body:** Must match `docs/EVENT_SCHEMA.md`
   ```json
   {
     "eventId": "uuid",
     "projectId": "string",
     "type": "log | error | span | token_usage | ...",
     "timestamp": "ISO8601",
     "sdk": { "name": "string", "version": "string" },
     "context": {},
     "body": {}
   }
   ```
3. **Validation:** Use Pydantic to validate incoming events
4. **Response:** Return `202 Accepted` with `{ "status": "queued", "eventId": "..." }`
5. **For Now:** Just print to console (no Redis yet)

**Acceptance Criteria:**
- [ ] Server starts with `uvicorn main:app --reload`
- [ ] POST to `/api/v1/events` with valid JSON returns 202
- [ ] POST with invalid JSON returns 422 with validation errors
- [ ] Health check endpoint `/health` returns 200

---

### Task 4: API Key Authentication 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create/Modify:**
- `/services/ingest-api/auth.py` — API key validation logic
- `/services/ingest-api/middleware.py` — Auth middleware

**Detailed Requirements:**
1. **Header:** `X-API-Key: sk_live_xxxx` or `Authorization: Bearer sk_live_xxxx`
2. **Validation:** Check key format, check key exists in DB (mock for now)
3. **Project Scoping:** Extract `project_id` from key and inject into request
4. **Rate Limiting:** (Optional) Basic rate limit per key

**Acceptance Criteria:**
- [ ] Request without API key returns 401
- [ ] Request with invalid key returns 403
- [ ] Request with valid key passes through to endpoint

---

## Phase 2: Storage Layer (Days 4-7)

### Task 5: Redis Queue Integration 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create/Modify:**
- `/services/ingest-api/queue.py` — Redis client wrapper
- Modify `/services/ingest-api/routes/events.py` — Push to queue instead of print

**Detailed Requirements:**
1. Connect to Redis using `REDIS_URL` from config
2. Push validated events to a Redis Stream (`events:incoming`)
3. Use `XADD` command for ordered, durable ingestion
4. Handle connection failures gracefully (return 503)

**Acceptance Criteria:**
- [ ] Events appear in Redis Stream after POST
- [ ] Can view events with `redis-cli XREAD`
- [ ] API returns 503 if Redis is down

---

### Task 6: Processor Worker 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/services/processor/main.py` — Worker entry point
- `/services/processor/consumer.py` — Redis Stream consumer
- `/services/processor/handlers.py` — Event processing logic

**Detailed Requirements:**
1. Read from Redis Stream (`events:incoming`) using consumer groups
2. Parse event, enrich with metadata (timestamp normalization, cost estimation)
3. Write to ClickHouse (or print for now)
4. Acknowledge message after successful processing

**Acceptance Criteria:**
- [ ] Worker starts and connects to Redis
- [ ] Worker consumes events from stream
- [ ] Worker handles errors without crashing

---

### Task 7: ClickHouse Schema & Writer 🔲
**Status:** Not Started
**Model:** Claude Opus 4.5 (Architect) + Sonnet (Coder)
**Files to Create:**
- `/services/processor/clickhouse.py` — ClickHouse client
- `/infra/clickhouse/schema.sql` — Table definitions

**Detailed Requirements:**
1. **Events Table:**
   ```sql
   CREATE TABLE events (
     event_id UUID,
     project_id String,
     type String,
     timestamp DateTime64(3),
     body String, -- JSON blob
     created_at DateTime DEFAULT now()
   ) ENGINE = MergeTree()
   ORDER BY (project_id, timestamp);
   ```
2. **Batched Writes:** Batch events (100 or 1 second, whichever first)
3. **Connection Pooling:** Reuse connections

**Acceptance Criteria:**
- [ ] Schema can be applied to ClickHouse
- [ ] Events are queryable after ingestion
- [ ] `SELECT count() FROM events` works

---

## Phase 3: Dashboard (Days 8-14)

### Task 8: Query API 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/services/ui-backend/main.py` — FastAPI for dashboard queries
- `/services/ui-backend/routes/events.py` — List/search events
- `/services/ui-backend/routes/stats.py` — Aggregation queries

**Detailed Requirements:**
1. **Endpoints:**
   - `GET /api/v1/events?project_id=&limit=&offset=` — Paginated list
   - `GET /api/v1/events/{event_id}` — Single event detail
   - `GET /api/v1/stats/overview?project_id=` — Request count, error rate, token usage
2. **Auth:** Validate session/API key (can be same as ingest or separate)

**Acceptance Criteria:**
- [ ] Can list events for a project
- [ ] Can view single event with full body
- [ ] Stats endpoint returns aggregated numbers

---

### Task 9: Frontend — Project Setup 🔲
**Status:** Not Started
**Model:** GPT-4o (Fast) for setup, Sonnet for components
**Files to Create:**
- `/web/package.json`
- `/web/src/App.tsx`
- `/web/src/main.tsx`
- `/web/vite.config.ts`
- `/web/tailwind.config.js`

**Detailed Requirements:**
1. React + TypeScript + Vite
2. Tailwind CSS for styling
3. React Router for navigation
4. Basic folder structure: `/components`, `/pages`, `/hooks`, `/api`

**Acceptance Criteria:**
- [ ] `npm run dev` starts the app
- [ ] Basic "Hello World" renders

---

### Task 10: Frontend — Events Timeline 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/web/src/pages/EventsPage.tsx`
- `/web/src/components/EventList.tsx`
- `/web/src/components/EventCard.tsx`
- `/web/src/api/events.ts`

**Detailed Requirements:**
1. Fetch events from Query API
2. Display as a timeline (newest first)
3. Show: timestamp, type, model, status indicator
4. Click to expand and see full event body
5. Basic filters: type, date range

**Acceptance Criteria:**
- [ ] Events load and display
- [ ] Can filter by event type
- [ ] Can click to see details

---

### Task 11: Frontend — Stats Dashboard 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/web/src/pages/DashboardPage.tsx`
- `/web/src/components/StatCard.tsx`
- `/web/src/components/Chart.tsx` (use recharts or chart.js)

**Detailed Requirements:**
1. Display key metrics:
   - Total requests (today, 7 days, 30 days)
   - Error rate percentage
   - Token usage (input/output)
   - Estimated cost (USD)
2. Simple line chart for requests over time

**Acceptance Criteria:**
- [ ] Numbers display correctly
- [ ] Chart renders with real data

---

## Phase 4: SDK & Alerts (Days 15-21)

### Task 12: Python SDK 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/libs/sdk-python/lynex/__init__.py`
- `/libs/sdk-python/lynex/client.py`
- `/libs/sdk-python/lynex/events.py`
- `/libs/sdk-python/setup.py` or `pyproject.toml`

**Detailed Requirements:**
1. **Initialize:**
   ```python
   import lynex
   lynex.init(api_key="sk_live_xxx", project_id="proj_xxx")
   ```
2. **Capture Event:**
   ```python
   lynex.capture_llm_call(
       model="gpt-4",
       prompt="Hello",
       response="Hi there!",
       tokens={"input": 5, "output": 10},
       latency_ms=230
   )
   ```
3. **Auto-batching:** Queue events, flush every 1 second or 10 events
4. **Graceful shutdown:** Flush on program exit

**Acceptance Criteria:**
- [ ] Can install with `pip install -e .`
- [ ] Events appear in dashboard after SDK call
- [ ] No exceptions thrown in normal use

---

### Task 13: JavaScript SDK 🔲
**Status:** Not Started
**Model:** Claude Sonnet 4.5
**Files to Create:**
- `/libs/sdk-js/src/index.ts`
- `/libs/sdk-js/src/client.ts`
- `/libs/sdk-js/package.json`
- `/libs/sdk-js/tsconfig.json`

**Detailed Requirements:**
1. **Initialize:**
   ```javascript
   import { lynex } from 'lynex';
   const client = new lynex({ apiKey: 'sk_live_xxx', projectId: 'proj_xxx' });
   ```
2. **Capture Event:**
   ```javascript
   client.captureLLMCall({
     model: 'gpt-4',
     prompt: 'Hello',
     response: 'Hi there!',
     tokens: { input: 5, output: 10 },
     latencyMs: 230
   });
   ```
3. **Works in Node.js and Browser**

**Acceptance Criteria:**
- [ ] Can install with `npm install`
- [ ] Events appear in dashboard
- [ ] TypeScript types are correct

---

### Task 14: Basic Alerting 🔲
**Status:** Not Started
**Model:** Claude Opus 4.5 (Architect) + Sonnet (Coder)
**Files to Create:**
- `/services/processor/alerts.py` — Alert rule engine
- `/services/processor/notifiers/webhook.py` — Webhook sender
- `/services/processor/notifiers/email.py` — Email sender (optional)

**Detailed Requirements:**
1. **Alert Rules:**
   - Error rate > X% in Y minutes
   - Token usage > Z in Y minutes
   - Specific error type detected
2. **Actions:**
   - Send webhook (Slack, Discord, custom)
   - Send email (via SendGrid or similar)
3. **Cooldown:** Don't spam alerts (once per 5 minutes per rule)

**Acceptance Criteria:**
- [ ] Alert triggers when error rate spikes
- [ ] Webhook is sent to configured URL
- [ ] No duplicate alerts within cooldown period

---

## Phase 5: Polish & Launch (Days 22-28)

### Task 15: Project & API Key Management 🔲
**Status:** Not Started
**Files to Create:**
- `/services/ui-backend/routes/projects.py`
- `/services/ui-backend/routes/api_keys.py`
- `/web/src/pages/SettingsPage.tsx`

**Detailed Requirements:**
1. Create/list/delete projects
2. Generate/revoke API keys per project
3. Show usage per key

---

### Task 16: User Authentication 🔲
**Status:** Not Started
**Files to Create:**
- Integration with Appwrite (or simple JWT)
- `/web/src/pages/LoginPage.tsx`
- `/web/src/pages/SignupPage.tsx`

**Detailed Requirements:**
1. Sign up with email/password
2. Login and get session
3. Protect dashboard routes

---

### Task 17: Billing Integration 🔲
**Status:** Not Started
**Files to Create:**
- `/services/billing/main.py`
- Stripe integration

**Detailed Requirements:**
1. Free tier: 50k events/month
2. Pro tier: 500k events/month
3. Usage tracking and overage handling

---

### Task 18: Deployment 🔲
**Status:** Not Started
**Files to Create:**
- `/infra/digitalocean/` — Deployment scripts
- `/.github/workflows/deploy.yml` — CI/CD pipeline

**Detailed Requirements:**
1. Deploy Ingest API to DigitalOcean App Platform (or Droplet)
2. Deploy Frontend to Vercel/Netlify
3. Set up domain (from Namecheap Student Pack)
4. Configure SSL

---

## Progress Tracker

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1. Foundation | 4 | 2 | 🟡 In Progress |
| 2. Storage | 3 | 0 | ⚪ Not Started |
| 3. Dashboard | 4 | 0 | ⚪ Not Started |
| 4. SDK & Alerts | 3 | 0 | ⚪ Not Started |
| 5. Polish | 4 | 0 | ⚪ Not Started |

**Total: 18 Tasks**

---

## Quick Reference: What to Say to the AI

### Starting a New Task
```
I am building Lynex. Current context:
- docs/CONTEXT.md (product spec)
- docs/SYSTEM.md (coding rules)
- docs/ARCHITECTURE.md (tech stack)
- docs/EVENT_SCHEMA.md (data shapes)

I am now working on Task [X]: [Task Name].
Here are the requirements: [Copy from above]
Please create the files.
```

### When Something Breaks
```
I ran the code and got this error:
[Paste error]

Here is the file:
[Paste file content]

Fix it and explain why it broke.
```

### Before Moving to Next Task
```bash
git add .
git commit -m "feat: [task description]"
```

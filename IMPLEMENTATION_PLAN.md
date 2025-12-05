# Implementation Plan: Path to Production Readiness

This plan outlines the step-by-step actions required to transform the WatchLLM codebase from an MVP scaffold into a production-ready observability platform.

---

## Phase 1: Critical Fixes & Stability (Week 1)

**Goal:** Fix broken services, patch security vulnerabilities, and ensure data reliability.

### 1. Fix Billing Service
- [x] **Fix Syntax Errors**: Correct the duplicate return statement in `services/billing/billing.py`.
- [x] **Fix Duplicate Functions**: Remove the duplicate `get_subscription` definition.
- [x] **Fix Imports**: Uncomment and correct imports in `services/billing/main.py` for `get_usage_stats`, `check_usage_limit`, etc.
- [x] **Implement Missing Logic**:
    - [x] Initialize the `WHOP_WEBHOOK_SECRET` and `subscriptions` in-memory fallback (or remove if MongoDB is mandatory).
    - [x] Implement `get_usage_stats` and `check_usage_limit` properly.
- [x] **Add Monthly Reset**: Create a simple mechanism (lazy check or background task) to reset `events_used_this_period` when a new billing period starts.

### 2. Fix SQL Injection in UI Backend
- [x] **Audit Queries**: Identify all instances of f-string SQL construction in `services/ui-backend/clickhouse.py`.
- [x] **Parameterize Queries**: Rewrite queries to use ClickHouse driver parameter substitution (e.g., `%(project_id)s`).
- [x] **Validate Inputs**: Ensure `order_by` and other dynamic fields are whitelisted, not user-supplied strings.

### 3. Fix Alerts System
- [x] **Fix Project ID Bug**: Update `services/processor/alerts.py` to consistently use `project_id` (snake_case) matching the event schema, instead of `projectId` (camelCase).
- [x] **Persist Rules**:
    - [x] Create a MongoDB collection for `alert_rules`.
    - [x] Update `AlertManager` to load rules from MongoDB on startup and refresh periodically.
    - [x] Create API endpoints in `ui-backend` to CRUD alert rules.

### 4. SDK Reliability (Retries)
- [ ] **Python SDK**:
    - [ ] Add `tenacity` dependency.
    - [ ] Wrap the `_worker` loop's request logic with a retry decorator (exponential backoff, max 3 retries).
- [ ] **JS SDK**:
    - [ ] Implement a retry loop in the `flush` method with exponential backoff (e.g., 1s, 2s, 4s).
    - [ ] Add a `maxRetries` configuration option.

---

## Phase 2: Core Observability Features (Weeks 2-4)

**Goal:** Implement the primary value proposition: visualizing AI agent execution.

### 1. Trace Visualization (Backend)
- [ ] **Schema Update**: Ensure `events` table has `trace_id` and `parent_event_id` columns (already in schema, verify usage).
- [ ] **Trace API**:
    - [ ] Create `GET /api/v1/traces/{trace_id}` endpoint in `ui-backend`.
    - [ ] Implement ClickHouse query to fetch all events for a given `trace_id`, ordered by timestamp.
    - [ ] Construct a tree structure (waterfall) from the flat event list.
- [ ] **Trace List API**:
    - [ ] Create `GET /api/v1/traces` endpoint to list recent traces (grouped by `trace_id`).

### 2. Trace Visualization (Frontend)
- [ ] **Trace List Page**: Create a new page to list traces with summary stats (latency, token cost, error count).
- [ ] **Trace Detail View**:
    - [ ] Implement a Waterfall chart component (using Recharts or custom SVG).
    - [ ] Show span details on click (inputs, outputs, metadata).
    - [ ] Highlight errors in red.

### 3. Agent Step Debugger
- [ ] **Step Indexing**: Ensure `agent_action` events include a `step_index` or logical sequence number.
- [ ] **Debug UI**:
    - [ ] Create a "Replay" view for a trace.
    - [ ] Allow stepping forward/backward through events.
    - [ ] Show the state of the agent at each step (context, memory).

### 4. Automated Tests
- [ ] **Test Infrastructure**:
    - [ ] Add `pytest` and `httpx` to `requirements.txt` for all services.
    - [ ] Create `conftest.py` with fixtures for MongoDB and ClickHouse mocks.
- [ ] **Unit Tests**:
    - [ ] Write tests for `ingest-api` event validation.
    - [ ] Write tests for `billing` logic (subscription limits).
    - [ ] Write tests for `processor` alert evaluation.
- [ ] **Integration Tests**:
    - [ ] Create a docker-compose test profile.
    - [ ] Write an E2E test that sends an event via SDK and verifies it in the `ui-backend` response.

---

## Phase 3: User Experience & Enterprise Features (Month 2)

**Goal:** Make the platform usable for teams and sellable to enterprises.

### 1. Alert Configuration UI
- [ ] **Frontend Page**: Create `AlertsPage.tsx`.
- [ ] **Rule Builder**: UI to define rules (Event Type, Condition, Threshold, Channel).
- [ ] **Integration**: Connect to the new Alert CRUD API.

### 2. RBAC Implementation
- [ ] **Data Model**: Add `roles` field to `User` model and `members` list to `Project` model.
- [ ] **Middleware**: Update `supabase_middleware.py` to check project membership and permissions.
- [ ] **Frontend**: Hide admin actions (e.g., "Delete Project", "Billing") for non-admin users.

### 3. Project Management
- [ ] **Project Selector**: Add a dropdown in the top navigation to switch the active `project_id`.
- [ ] **Context**: Store selected project in React Context/Local Storage.
- [ ] **Create/Edit UI**: Implement forms to create new projects and rename existing ones.

---

## Phase 4: Advanced Features (Month 3)

**Goal:** Add competitive differentiators and operational maturity.

### 1. Prompt Diffing
- [ ] **Versioning**: When a `model_response` event includes prompt template metadata, store the template in a `prompt_versions` table.
- [ ] **Diff UI**: Create a view to compare two versions of a prompt template side-by-side, highlighting changes.

### 2. Cold Storage (S3)
- [ ] **Infrastructure**: Add MinIO (local) or S3 (prod) configuration.
- [ ] **Archival Job**: Create a cron job in `processor` to:
    - [ ] Select events older than 30 days from ClickHouse.
    - [ ] Export to Parquet format.
    - [ ] Upload to S3.
    - [ ] Delete from ClickHouse.

### 3. Prometheus Metrics
- [ ] **Instrumentation**: Add `prometheus-client` to all Python services.
- [ ] **Metrics**: Expose `/metrics` endpoint.
- [ ] **Counters**: Track `events_ingested_total`, `events_processed_total`, `errors_total`, `processing_latency_seconds`.
- [ ] **Grafana**: Create a standard dashboard JSON for platform health.

---

## Immediate Next Step

I am ready to start with **Phase 1, Task 1: Fix Billing Service**. Shall I proceed with fixing the syntax errors and duplicate functions in `services/billing/billing.py`?

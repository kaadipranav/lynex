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
- [x] **Python SDK**:
    - [x] Add `tenacity` dependency.
    - [x] Wrap the `_worker` loop's request logic with a retry decorator (exponential backoff, max 3 retries).
- [x] **JS SDK**:
    - [x] Implement a retry loop in the `flush` method with exponential backoff (e.g., 1s, 2s, 4s).
    - [x] Add a `maxRetries` configuration option.

---

## Phase 2: Core Observability Features (Weeks 2-4)

**Goal:** Implement the primary value proposition: visualizing AI agent execution.

### 1. Trace Visualization (Backend)
- [x] **Schema Update**: Ensure `events` table has `trace_id` and `parent_event_id` columns (already in schema, verify usage).
- [x] **Trace API**:
    - [x] Create `GET /api/v1/traces/{trace_id}` endpoint in `ui-backend`.
    - [x] Implement ClickHouse query to fetch all events for a given `trace_id`, ordered by timestamp.
    - [x] Create `GET /api/v1/traces` endpoint to list recent traces.
- [x] **Span Hierarchy Reconstruction**:
    - [x] Build tree structure from flat event list using `parent_event_id`.
    - [x] Calculate trace duration and metadata.

### 2. Trace Visualization (Frontend)
- [x] **Trace List Page**:
    - [x] Create `TracesPage.tsx` to list recent traces with summary data.
    - [x] Display trace_id, duration, event count, cost, and status.
- [x] **Trace Detail Page**:
    - [x] Create `TraceView.tsx` component for hierarchical span visualization.
    - [x] Implement collapsible tree view with indentation.
    - [x] Color-code spans by type (span, error, model_response, etc.).
    - [x] Add click-to-inspect functionality for span details.
- [x] **Navigation**:
    - [x] Add "Traces" link to navigation bar.
    - [x] Add routes for `/traces` and `/traces/:traceId`.

### 3. Cost Attribution
- [x] **Pricing Table**:
    - [x] Create `pricing.py` module with comprehensive model pricing data.
    - [x] Include pricing for GPT-4, Claude, Gemini, Mistral, Cohere models.
    - [x] Implement `PricingCalculator` class with cost calculation logic.
- [x] **Cost Enrichment**:
    - [x] Update `handlers.py` to use pricing calculator for token_usage events.
    - [x] Add `estimated_cost_usd` field to enriched events.
    - [x] Include cost breakdown (input_cost, output_cost) when available.
- [x] **Model Name Normalization**:
    - [x] Handle versioned model names (e.g., "gpt-4-0125-preview" → "gpt-4").
    - [x] Fallback to default pricing for unknown models.

### 4. Batch Ingestion
- [x] **Batch Endpoint**: `POST /api/v1/events/batch` (already implemented)
    - [x] Accept up to 100 events per request.
    - [x] Queue all events atomically.
    - [x] Return batch status and event IDs.

### 5. Agent Step Debugger
- [ ] **Step Indexing**: Ensure `agent_action` events include a `step_index` or logical sequence number.
- [ ] **Debug UI**:
    - [ ] Create a "Replay" view for a trace.
    - [ ] Allow stepping forward/backward through events.
    - [ ] Show the state of the agent at each step (context, memory).

### 6. Automated Tests
- [x] **Test Infrastructure**:
    - [x] Created `conftest.py` with fixtures for MongoDB, ClickHouse, and Redis mocks.
    - [x] Added `pyproject.toml` with pytest configuration.
    - [x] Created `requirements-test.txt` with test dependencies.
- [x] **Unit Tests**:
    - [x] `test_ingest_api.py` - Event validation, schema tests, batch validation.
    - [x] `test_billing.py` - Subscription logic, usage limits, monthly reset.
    - [x] `test_processor.py` - Pricing calculation, alert evaluation, event enrichment.
- [x] **Integration Tests**:
    - [x] `test_e2e_flow.py` - End-to-end event ingestion pipeline tests.
    - [ ] Write an E2E test that sends an event via SDK and verifies it in the `ui-backend` response.

---

## Phase 3: User Experience & Enterprise Features (Month 2)

**Goal:** Make the platform usable for teams and sellable to enterprises.

### 1. Alert Configuration UI
- [x] **Frontend Page**: Created `AlertsPage.tsx` with rule builder UI.
- [x] **Rule Builder**: Form to define rules (Event Type, Condition, Threshold, Channel).
- [x] **Integration**: Connected to Alert CRUD API (routes/alerts.py).
- [x] **Navigation**: Added "Alerts" link to navigation bar and routing.

### 2. RBAC Implementation
- [x] **Data Model**: Added `roles` field to `User` model and `members` list to `Project` model.
- [x] **Backend**: Created comprehensive RBAC system in `routes/projects.py` with role hierarchy.
- [x] **Permissions**: Implemented `check_permission()` and `verify_project_access()` helpers.
- [x] **Roles**: OWNER, ADMIN, MEMBER, VIEWER with proper permission levels.

### 3. Project Management
- [x] **Project Selector**: Created `ProjectSelector.tsx` dropdown component in navigation.
- [x] **Context**: Implemented `useProject` hook with React Context and localStorage persistence.
- [x] **Create/Edit UI**: Full project creation modal with name and description.
- [x] **Backend API**: Complete CRUD operations in `routes/projects.py`:
  - [x] List projects (filtered by user access)
  - [x] Create project (user becomes owner)
  - [x] Update project (requires ADMIN)
  - [x] Delete project (requires OWNER, soft delete)
  - [x] Add/Remove members (requires ADMIN)
  - [x] Update member roles (requires ADMIN)

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

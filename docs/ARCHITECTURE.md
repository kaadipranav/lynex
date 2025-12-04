# ARCHITECTURE — High-Level System Design

> Purpose: Define the technical architecture decisions, component interactions, data flow, scaling strategies, and infra requirements for the AI observability platform. This document ensures consistency across generated code and infra, and serves as the canonical reference for engineers and AI agents.

---

## 1. Architectural goals

* **Scalable ingestion**: ingest millions of events per day with low latency.
* **Cost-effective storage**: hot path for recent queries, cold archive for long-term retention.
* **Low-latency UI**: dashboard queries should be snappy for 30‑day retention windows.
* **Fault isolation**: failures in one tenant must not impact others.
* **Extensibility**: support new event types, models, and integrations easily.
* **Security & compliance**: data residency, encryption, RBAC, audit trails.

---

## 2. System components (overview)

```
+-----------------+       +-----------------+       +-----------------+
|  Client SDKs    |  -->  |  Ingest API     |  -->  |  Stream Queue   |
| (py/js/curl)    |       | (FastAPI)       |       |  (Redis/Kafka)  |
+-----------------+       +-----------------+       +-----------------+
                                    |                      |
                                    v                      v
                              +----------------+     +----------------+
                              | Processor(s)   |     | Metrics Worker |
                              | (workers)      |     | (aggregations) |
                              +----------------+     +----------------+
                                    |                      |
                                    v                      v
                            +--------------------+   +-------------------+
                            | Hot storage (ClickHouse,
                            |  Elasticsearch, or Timescale) |
                            +--------------------+   +-------------------+
                                    |                      |
                                    v                      v
                             +------------------+     +------------------+
                             | API & Query Svc  | --> | Frontend (React) |
                             +------------------+     +------------------+
                                    |
                                    v
                              +---------------+
                              | Billing + Auth |
                              +---------------+

S3 cold archive, backups, CI/CD and infra not shown.
```

---

## 3. Detailed components

### 3.1 Client SDKs

* Lightweight packages for Python and JS.
* Responsibilities:

  * Validate payloads against `EVENT_SCHEMA.json`.
  * Batch & compress events for network efficiency.
  * Provide guaranteed delivery semantics with retries and idempotency via `event_id`.
  * Provide sync & async APIs (Python) and promise APIs (JS).
* Security: supports API key auth and optional JWT for server-to-server.

### 3.2 Ingest API

* FastAPI-based Python service.
* Responsibilities:

  * Receive events, validate, enrich (add metadata), rate-limit, and push to stream queue.
  * Respond quickly with `202 Accepted` for fire-and-forget ingestion.
  * Authenticate requests using API keys and project scoping.
  * Provide a debug/local mode for devs to test ingestion.
* Horizontal autoscaling behind a load balancer.

### 3.3 Stream Queue

* Start with **Redis Streams** for MVP (simplicity) and allow migration to **Kafka** for high-throughput needs.
* Responsibilities:

  * Durable, ordered ingestion buffer.
  * Backpressure handling for downstream processors.

### 3.4 Processor Workers

* Stateless worker fleet (Python, async) consuming from stream queue.
* Responsibilities:

  * Normalize events, enrich with model metadata (e.g. model fingerprints), compute cost estimates, run heuristic detectors (hallucination risk), and store into hot storage and S3 archive.
  * Emit metrics to Prometheus and errors to internal Sentry.
  * Execute synthetic monitors and scheduled checks.

### 4. Infrastructure Strategy (Student Pack Edition)

Leveraging the GitHub Student Developer Pack allows us to run a production-grade cluster for $0/year.

*   **Compute (Ingest + Workers):** **DigitalOcean** ($200 credit).
    *   Use Droplets for the Ingestion API and Processor Workers.
    *   Avoids serverless cold starts and allows high-throughput buffering.
*   **Auth & User Management:** **Appwrite** (Free Education Plan).
    *   Handles JWT generation, user accounts, teams, and RBAC.
    *   Replaces custom "Billing + Auth" service complexity for MVP.
*   **Operational Monitoring:** **Datadog** (Free Pro, 2 years) + **Sentry** (Free Student Tier).
    *   Monitor the *platform's* health (CPU, RAM, Error Rates) using enterprise tools for free.
*   **DNS & SSL:** **Namecheap** (.me/.tech domain) + **Cloudflare** (Free).
*   **Database Hosting:**
    *   **Metadata:** Self-hosted PostgreSQL on DigitalOcean OR Managed MongoDB (Atlas $50 credit).
    *   **Analytics:** Self-hosted **ClickHouse** on DigitalOcean (high RAM droplet).

---

## 5. Data Flow

1.  **SDK** sends JSON event to `api.lynex.dev` (DigitalOcean LB).
2.  **Ingest API** validates API Key (cached from Appwrite/DB) -> pushes to **Redis** (DO Droplet).
3.  **Worker** pulls from Redis -> enriches -> inserts into **ClickHouse** (DO Droplet).
4.  **Worker** checks alerts -> sends webhook/email.
5.  **Frontend** (Vercel/Netlify) queries **Ingest API** (which queries ClickHouse) to render charts.
  * Efficient aggregations for cost/latency dashboards.
* Storage pattern:

  * Recent 30 days in hot store (fast queries)
  * Older data archived to S3 + Parquet and rehydrated on-demand.

### 3.6 API & Query Service

* GraphQL or REST service for dashboard queries and SDK management.
* Responsibilities:

  * Query hot store and assemble timelines, charts, and filters.
  * Authenticate users and enforce RBAC.
  * Provide pagination, sorting, and faceting for large result sets.

### 3.7 Frontend

* React + TypeScript using Vite for dev speed.
* Responsibilities:

  * Dashboard UI: timeline, prompt diff, cost charts, toolcall visualizer.
  * Alerts management, project settings, API keys UI.
  * Lightweight client-side caching of recent queries.

### 3.8 Billing & Auth

* Stripe for billing, WHOP integration for distribution and plugin store.
* Authentication: email/password (dev), SSO (enterprise), API keys for ingestion.
* RBAC & team management with SCIM support for enterprise.

### 3.9 Cold Archive

* S3 bucket with lifecycle policies to move older data to Glacier.
* Stored in Parquet for efficient rehydration and analytics.

### 3.10 Observability & Platform Health

* Prometheus metrics, Grafana dashboards, internal Sentry for platform errors.
* Alerts for sustained high error rate, queue backlog, and DB latency.

---

## 4. Multi-tenant design

* **Tenant isolation:** logical isolation via `project_id`; per-tenant encryption keys are supported for enterprise.
* **Storage:** index tenant_id as a primary filter for queries; avoid cross-tenant joins.
* **Rate-limiting:** per-tenant and per-api-key rate limiting.

---

## 5. Data flow (step-by-step)

1. Client SDK validates event and sends to `POST /v1/projects/{project_id}/events`.
2. Ingest API authenticates and enqueues to Redis Stream.
3. Processor reads from stream, normalizes event, computes derived metrics, runs detectors, and writes to hot store and S3 archive.
4. Query service reads from hot store to display dashboards.
5. Billing service consumes usage events (tokens/cost) to charge customers.
6. Alerts are triggered based on metrics and events; notifications are sent via Slack, email, or webhooks.

---

## 6. Scaling strategy

### Phase 1 (MVP)

* Redis streams, ClickHouse small instance, Postgres for metadata, S3 cold storage.
* Horizontal autoscaling of ingest and processor services.
* Single region deploy (e.g., GCP/US or AWS) with multi-AZ for resilience.

### Phase 2 (Growth)

* Move to Kafka for ingest if throughput > 100k events/min.
* Partition hot store by tenant or time for performance.
* Add read replicas for query service.

### Phase 3 (Enterprise)

* Multi-region deployment options, VPC peering, dedicated infra for large customers, and on-prem options.
* Enterprise customers may require private networking and custom retention policies.

---

## 7. Reliability & SLOs

* **Ingest availability:** 99.95% SLA for ingestion API.
* **Event durability:** `at-least-once` delivery guarantee for events persisted to hot store.
* **Query latency:** 95th percentile under 1 second for 7-day window queries.
* **Processing latency:** P95 under 10 seconds from ingestion to hot store for standard events.

---

## 8. Security & compliance details

* Use per-project encryption keys for enterprise (KMS/HSM).
* Data residency: offer region selection at project creation.
* Retention & deletion workflows: immediate deletion endpoints; background scrubbing jobs.

---

## 9. Backup & DR

* Daily DB backups (Postgres), incremental snapshots for ClickHouse.
* S3 versioning and lifecycle rules.
* DR runbook for failover to read-only mode and alert customers.

---

## 10. Extensibility & plug-in model

* Use an events-based plugin system where integrations (Slack, Datadog, webhook, RAG verification) subscribe to event topics.
* Plugin sandboxing and throttling for third-party handlers.

---

## 11. Cost optimization

* Sampling of raw texts for high-volume customers; aggregate metrics stored for all.
* Tiered cold vs hot storage.
* Precompute heavy aggregations during low-traffic hours.

---

## 12. Appendix: tech choices (recommended stack)

* Language: Python 3.11 (backend), TypeScript (frontend)
* Ingest: FastAPI + uvicorn
* Queue: Redis Streams -> Kafka (future)
* Hot store: ClickHouse or Elasticsearch
* Metadata DB: Postgres
* Object storage: S3
* Metrics: Prometheus + Grafana
* CI/CD: GitHub Actions
* Containerization: Docker + Kubernetes (EKS/GKE/AKS)

---

*End of ARCHITECTURE.md*

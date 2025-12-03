# SYSTEM — Developer System & AI Agent Rules

> Purpose: this file is the authoritative "how to build" guide. It contains the coding standards, agent behavior rules, repository layout, CI/CD rules, security constraints, and conventions that any human or AI agent must follow when modifying the codebase.

---

## 1. High-level rules for AI agents (non-negotiable)

1. **Read before you write.** The agent MUST read `/docs/CONTEXT.md`, `/docs/PRD.md`, `/docs/API_SPEC.yaml`, `/docs/EVENT_SCHEMA.json`, and `/docs/CODING_GUIDE.md` before proposing or writing any code. If any referenced file is missing, the agent must create it in `/docs/` using the project's naming conventions.
2. **Small, incremental changes.** Every code generation step must modify at most 3 new or existing files per commit. Prefer adding new modules rather than refactoring large sections at once.
3. **One feature → one branch → one PR.** Each logical feature or bug fix must live in a separate git branch with a single, focused Pull Request and a clear description.
4. **Do not delete files without explicit instruction.** The agent can deprecate but must keep history. Deletions require a human review flag in the PR title: `DESTRUCTIVE: requires human approval`.
5. **Automated tests first.** Any feature that changes logic must include unit tests and integration tests. The agent must add tests before or alongside implementation.
6. **No secrets in code.** The agent must never emit API keys, private tokens, or secrets in code or docs. Secrets must reference environment variables (see section on env vars).
7. **Use the coding guide.** Format, lint, and commit rules in `/docs/CODING_GUIDE.md` are mandatory. Generated code must pass linters and tests locally before PR creation.
8. **Backward compatibility.** When changing public APIs or SDK contracts, the agent must create a compatibility shim and bump the API version as per `/docs/API_VERSIONING.md` (semver rules).
9. **Explain changes in PR body.** The agent must include a changelog entry and a clear `Why` and `How` section in the PR description.
10. **No external network calls during code generation.** The agent may not contact external services for execution; it should rely on provided docs and mock implementations for tests. (Runtime infra may call external APIs only during deployment by humans.)

---

## 2. Repo layout (canonical)

```
/ (repo root)
├─ /docs
│  ├─ CONTEXT.md
│  ├─ PRD.md
│  ├─ API_SPEC.yaml
│  ├─ EVENT_SCHEMA.json
│  ├─ CODING_GUIDE.md
│  ├─ ARCHITECTURE.md
│  └─ SYSTEM.md
├─ /services
│  ├─ /ingest-api (python/fastapi)
│  ├─ /processor (worker: python/redis-kq or go/kafka)
│  ├─ /ui-backend (node/ts or python)
│  └─ /billing (stripe integration)
├─ /libs
│  ├─ /sdk-python
│  └─ /sdk-js
├─ /web (react app)
├─ /infra (terraform / k8s manifests)
├─ /tests
│  ├─ /integration
│  └─ /e2e
├─ .github (workflows)
├─ Dockerfile
└─ README.md
```

Notes: prefer separate service folders to keep single responsibility and to ease local testing.

---

## 3. Coding languages & frameworks (preferred)

* **Backend ingestion & workers:** Python 3.11 with FastAPI + uvicorn, or Node 18+/TypeScript with Fastify. Default: **Python** for ingestion/processing. Use pydantic for schemas.
* **Front-end:** React + TypeScript + Vite. Tailwind for styling.
* **SDKs:** Python (typed), JavaScript/TypeScript (typed), publish to PyPI and npm.
* **DB/Storage:** PostgreSQL for relational metadata; ClickHouse or Timescale for event analytics; S3 for cold archive.
* **Queue:** Redis streams or Kafka depending on scale. Start with Redis for MVP.
* **CI:** GitHub Actions.

---

## 4. Coding conventions (must follow)

### Python

* Use **Black** for formatting, **isort** for imports, **ruff** or **flake8** for linting.
* Type hints required for all functions and public APIs (mypy in CI).
* Exceptions: do not swallow exceptions silently. Use structured errors and return typed error objects.
* Use `pydantic.BaseModel` for event and API schemas.
* Async-first: prefer `async def` for IO-bound endpoints and workers.

### TypeScript

* Use `eslint` with recommended rules, `prettier` for formatting, `tsconfig` targeting `ES2022`.
* Strict mode ON: `strict: true`.
* Use readable, explicit types for public SDK APIs.

### Commit messages

* Use Conventional Commits format: `type(scope): short description`.

  * `feat()`, `fix()`, `chore()`, `docs()`, `refactor()`, `perf()`, `test()`.
* Example: `feat(ingest): add token-usage field to /events`.

### Branching

* `main` protected (requires PR + 1 review + passing checks).
* Feature branches: `feat/<short-description>`.
* Hotfix: `hotfix/<issue-id>`.

---

## 5. API & schema rules (high level)

* APIs must be **idempotent** where applicable and return appropriate status codes.
* Use **JSON:API-like** structure for responses: `{ "data": ..., "meta": {...} }`.
* Errors must follow a consistent structure: `{ "error": { "code": "ERR_CODE", "message": "...", "details": {...} } }`.
* All ingestion endpoints must validate against `docs/EVENT_SCHEMA.json` and reject bad payloads with `400` + structured error.
* Rate limit per API key (configurable); return `429` with `Retry-After` header.

---

## 6. Versioning & compatibility

* **SemVer** for public SDKs and `v1`, `v2` pathing for HTTP API.
* Breaking changes require a major version bump and compatibility shims for 6 months.
* SDKs must expose a `api_version` field and read server `min_supported_sdk` if needed.
* Maintain a `CHANGELOG.md` with Conventional Commits-based autogenerated entries (use `release-please` or `semantic-release`).

---

## 7. Testing & Quality Gates

* **Unit tests**: each new function must have unit tests covering normal & edge cases.
* **Integration tests**: critical paths (ingestion → processor → storage → query) must have automated CI integration tests.
* **E2E tests**: smoke flows for UI and API (login, create project, ingest sample events, view logs).
* **Coverage**: keep a minimum of **70%** code coverage for backend services; critical modules aim for 90%.
* **Security scans**: run dependency vulnerability checks in CI (dependabot + `safety` for Python).

CI must fail if linters or tests fail. PRs require passing CI to merge.

---

## 8. Secrets & Environment variables

* Use `.env` only for local development. In production use secret managers (Vault, AWS Secrets Manager, or cloud provider equivalent).
* Do not hardcode provider keys. Always reference via `ENV` names.

**Core env variables (example)**

```
# Ingestion service
AISENTRY_API_KEY=...
DATABASE_URL=postgres://...
REDIS_URL=redis://...
S3_BUCKET=...
STRIPE_SECRET_KEY=...
JWT_SECRET=...
ENV=production

# SDK build
PYPI_TOKEN=...
NPM_TOKEN=...
```

* The agent must use `os.getenv()` or configuration loaders and must fail early if required vars are missing.

---

## 9. Logging, Monitoring & Observability for the platform

* Use structured JSON logs with timestamp, level, service, trace_id, span_id, request_id, project_id, run_id.
* Capture breadcrumbs and errors to the platform's internal Sentry instance.
* Expose Prometheus metrics for key indicators (ingest_rate, error_rate, queue_depth, process_latency).
* Health endpoints: `/healthz` (readiness) and `/livez` (liveness).
* Alerts for high error rate, high queue depth, low consumer throughput, DB connection failures.

---

## 10. Security & privacy constraints

* All prompts/responses are sensitive. Default behavior: **redact sensitive fields** (emails, SSNs, phone numbers) before storage unless customer opts-in to store raw text.
* Tokenize & hash any user identifiers stored in events to prevent PII leakage.
* Provide an audit path and data deletion mechanism per project.
* Encryption at rest for database & object storage; TLS for all transit.

---

## 11. SDK design rules

* SDKs must be **lightweight** and **dependency minimal**.
* Expose sync and async APIs for Python; callbacks and promises for JS.
* Default to non-blocking behavior: SDK calls should never block app execution — use fire-and-forget with optional `await` for guaranteed delivery.
* Provide retries with exponential backoff for transient failures and idempotency via `event_id`.
* SDKs must validate payloads client-side using `EVENT_SCHEMA.json` before sending.
* SDK versions must follow SemVer and include `CHANGELOG.md` and release notes.

---

## 12. Data retention & GDPR

* Configurable retention policies per project.
* Provide immediate export and deletion endpoints for account owners.
* Default retention: 90 days for free tier. Paid tiers increase retention windows.

---

## 13. Release & deployment process

* CI: run tests, linters, security scans.
* On merge to `main`, create a release candidate build and publish Docker images with `:sha` and `:latest` tags.
* Deploy to staging automatically. Production deploy requires a manual approval step.
* Rollback strategy: keep last 3 stable releases and allow one-click rollback in infra scripts.

---

## 14. Documentation standards

* All public APIs must have OpenAPI spec entries and example requests/responses.
* SDK docs must include quickstart, full API reference, and troubleshooting.
* Inline docstrings required for all public methods and classes.
* Keep `/docs` updated via CI checks: PR must update docs when API changes.

---

## 15. Performance & cost constraints

* CPU & memory budgets per service: specify in infra manifests (e.g., 0.5–2 CPU for small services initially).
* Define query performance SLOs: e.g., dashboard queries < 500ms P90 for 30-day index.
* Cost-control patterns: add sampling for raw response storage (store full text only for flagged items or sampled runs) and keep aggregate metrics for all runs.

---

## 16. Human-in-the-loop rules

* Sensitive operations (data deletion, destructive migrations, turning off redaction) must require a human approval step signed off by an authorized account.
* Add an admin audit trail for these actions.

---

## 17. PR template & checklist (agent must populate)

**PR Title:** `feat(<service>): short description` or `fix(...)`.

**PR body (must include):**

* Summary: what changed.
* Why: rationale.
* Tests: list of new/updated tests and how to run them.
* Docs: list doc files updated.
* Migration: DB migration steps (if any).

**Checklist:**

* [ ] Linting passed
* [ ] Tests passing
* [ ] Docs updated
* [ ] Schema validated against EVENT_SCHEMA.json
* [ ] No secrets

---

## 18. Emergency & incident response

* Incident channel: `#incidents` on Slack/Discord.
* Runbook pointer: `/docs/runbooks/ingestion_failure.md`.
* PagerDuty integration for Sev-1 incidents.
* Postmortem required within 72 hours for Sev-1 incidents.

---

## 19. How to instruct the AI agent (short guidance for operators)

When running an AI agent (Cursor/Claude/LLM) to generate code, always prefix with:

```
You are an internal code-generation agent. Before any modification, list the files you will change, why, and provide a single commit message. Then run tests locally (simulated). Create a draft PR with the changes. Follow `/docs/SYSTEM.md` and `/docs/CODING_GUIDE.md` strictly.
```

The agent must output a planned changelist and tests to run before producing the code.

---

## 20. Appendix: quick tools & suggested libs

### Python

* FastAPI, uvicorn, pydantic, httpx, aioredis, sqlalchemy/asyncpg, alembic, pytest, pytest-asyncio

### JS/TS

* Node 18+, Fastify or express + middy, axios, redis client, TypeORM/prisma (optional)

### Observability

* Prometheus client, OpenTelemetry SDK, Sentry (internal), Grafana

### Infra

* Terraform, k8s manifests, Docker, Helm

---

*End of SYSTEM.md*

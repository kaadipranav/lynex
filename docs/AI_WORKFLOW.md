# AI-Driven Development Workflow

> **Objective:** Build a production-grade AI observability platform without creating a "spaghetti code" mess.
> **Strategy:** Treat AI models as specialized employees. Delegate tasks based on their strengths. Maintain strict context discipline.

---

## 1. The "Model Roster" (Who does what)

Based on your available models, here is how you should assign tasks. Do not use one model for everything.

| Role | Best Model | Why? | When to use |
| :--- | :--- | :--- | :--- |
| **The Architect** | **Claude Opus 4.5** or **Gemini 3 Pro** | The "PhD" level reasoners. Massive context window, superior reasoning. Can hold the whole project structure in "head." | Planning features, writing documentation, deciding folder structures, breaking down big tasks. |
| **The Senior Coder** | **Claude Sonnet 4.5** or **GPT-5-Codex** | Currently the SOTA (State of the Art) for writing clean, bug-free code. Follows instructions perfectly. | Writing actual files (`.py`, `.tsx`), refactoring, writing tests. |
| **The Fast Worker** | **GPT-4o** or **Grok Code Fast** | Fast, cheap (computationally), good for simple logic. | Writing boilerplate, simple scripts, generating dummy data, explaining basic concepts. |
| **The Debugger** | **Claude Opus 4.5** or **GPT-5** | Deep reasoning capabilities to find "invisible" logic bugs. | When you have a weird error message and don't know why. |

---

## 2. The "Context First" Protocol (How to avoid mess)

The #1 reason AI projects fail is **Context Drift**. The AI forgets what file structure you have, or invents new libraries you aren't using.

### Rule 1: The "Context Dump"
Before starting **ANY** coding session, you must "prime" the AI. Do not assume it remembers yesterday.

**Copy-paste this prompt at the start of every chat:**
> "I am building Lynex. Here is the current context.
> 1. Project Goal: `docs/CONTEXT.md`
> 2. Tech Stack & Rules: `docs/SYSTEM.md`
> 3. Architecture: `docs/ARCHITECTURE.md`
> 4. Current Folder Structure: [Paste output of `tree` or `ls -R`]
>
> Acknowledge you have read this and wait for my next instruction."

### Rule 2: Docs Before Code
Never ask the AI to "Just build the login feature."
1.  **Update Docs:** Ask the **Architect** model to update `docs/ROADMAP.md` or create a mini-spec for the feature.
2.  **Generate Code:** Feed that spec to the **Coder** model.

---

## 3. The 4-Step Build Loop

Follow this loop for *every* single feature.

### Step 1: Plan (The Architect)
**Model:** Gemini 3 Pro / Claude 3.5 Sonnet
**Prompt:**
> "I need to build the [Feature Name, e.g., Ingestion API].
> Based on `docs/ARCHITECTURE.md`, list the exact files I need to create and the functions inside them.
> Don't write code yet, just the plan."

### Step 2: Code (The Senior Coder)
**Model:** Claude 3.5 Sonnet / GPT-5-Codex
**Prompt:**
> "Okay, let's implement the plan.
> Create the file `services/ingest-api/main.py`.
> Use the `EVENT_SCHEMA.md` as the source of truth for the data shape.
> Follow the coding style in `SYSTEM.md` (FastAPI, Pydantic, Typed).
> Output the full file content."

### Step 3: Verify & Fix (The Debugger)
**Action:** You run the code. It errors?
**Model:** GPT-5 / Gemini 3 Pro
**Prompt:**
> "I ran the code and got this error: [Paste Error].
> Here is the file content: [Paste File].
> Fix it and explain why it broke."

### Step 4: Commit (The Human)
**Action:** Once it works, run:
```bash
git add .
git commit -m "feat: added ingestion api"
```
*Never move to the next feature until the current one is committed.*

---

## 4. Immediate Next Steps (Phase 1 Execution)

We will now execute **Phase 1: The Skeleton**.

**Task 1: Repo Setup**
*   **Model:** GPT-4o (Fast)
*   **Prompt:** "Generate a script to create the folder structure defined in `docs/SYSTEM.md`. Create empty `__init__.py` files where needed."

**Task 2: Cloud Resources Setup (No Docker)**
*   **Model:** GPT-4o (Fast)
*   **Prompt:** "I am not using Docker. I will run Python locally and connect to cloud services.
    1. Create a `.env.example` file listing the connection strings I need (REDIS_URL, CLICKHOUSE_HOST, CLICKHOUSE_PASSWORD, etc.).
    2. Create a `config.py` in `services/ingest-api` that reads these env vars using `pydantic-settings`.
    3. Explain how to get a free Redis (Upstash) and ClickHouse (Tinybird or Aiven) URL for development."

**Task 3: The Ingest API (MVP)**
*   **Model:** Claude Sonnet 4.5 (Coder)
*   **Prompt:** "Write `services/ingest-api/main.py`. It should be a FastAPI app.
    1. Endpoint: POST /api/v1/event
    2. Validate payload using Pydantic (create schema based on `docs/EVENT_SCHEMA.md`).
    3. On success, print to console (we will add Redis later).
    4. Return 202 Accepted."

---

## 5. Emergency "Un-Mess" Button

If the code becomes a mess or you get confused:
1.  **Stop.**
2.  **Delete** the file that is broken.
3.  **Go back** to the **Architect** model.
4.  **Ask:** "I tried to build X and it failed. Here is my current file structure. How do I reset and try again simpler?"

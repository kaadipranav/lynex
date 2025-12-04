# Lynex - Local Development Guide

This guide will help you run the entire Lynex stack locally using Docker.

## Prerequisites

1. **Docker Desktop** installed and running.
2. **Git** installed.
3. **Node.js** (v18+) installed (for frontend).

## Step 1: Configure Environment

The `.env` file has been automatically configured with:
- Supabase credentials (from your project)
- Docker service URLs (redis://redis, mongodb://mongodb)
- Local ports

**Verify:** Check `d:\Lynex\.env` exists and has `SUPABASE_URL` set.

## Step 2: Start Backend Services

Run the following command in your terminal:

```bash
docker-compose up --build
```

This will start:
- **Ingest API** (http://localhost:8000)
- **UI Backend** (http://localhost:8001)
- **Billing Service** (http://localhost:8002)
- **Processor Worker** (Background)
- **ClickHouse** (http://localhost:8123)
- **Redis** (Port 6379)
- **MongoDB** (Port 27017)

**Wait until you see logs like:** `Application startup complete.`

## Step 3: Start Frontend

Open a **new terminal** window:

```bash
cd web
npm install
npm run dev
```

Access the dashboard at: **http://localhost:5173**

## Step 4: Test the Flow

1. **Login:** Go to http://localhost:5173/login
   - Use the "Sign Up" link to create a user (handled by Supabase).
   - Or use demo credentials if you set them up.

2. **Get API Key:**
   - Go to **Settings** page.
   - Create a new API Key.

3. **Send a Test Event:**

```bash
# Replace <YOUR_API_KEY> with the key from dashboard
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "event_type": "llm_completion",
    "model": "gpt-4",
    "tokens_input": 50,
    "tokens_output": 100,
    "latency_ms": 1200,
    "cost_usd": 0.0045,
    "status": "success"
  }'
```

4. **Verify:**
   - Check the **Dashboard** (refresh after 5s).
   - You should see the request count increase.

## Troubleshooting

- **"Connection refused"**: Ensure Docker is running.
- **"Missing API Key"**: Check `.env` file is loaded.
- **"Supabase Error"**: Verify your Supabase URL/Keys in `.env`.

## Stopping

Press `Ctrl+C` in the terminal running docker-compose.
To remove data: `docker-compose down -v`

# 🚀 Critical Environment Variables for App Startup

Based on analyzing your services (ingest-api, processor, billing, ui-backend), here are the **REQUIRED** environment variables to get the app running:

---

## ✅ **CRITICAL - App Won't Start Without These**

### 1. **Database - ClickHouse** (REQUIRED)
```bash
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=              # Can be empty for local dev
CLICKHOUSE_DATABASE=default
```

**Quick Start with Docker:**
```bash
docker run -d --name clickhouse -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
```

---

### 2. **Queue - Redis** (REQUIRED)
```bash
REDIS_URL=redis://localhost:6379
QUEUE_MODE=redis
```

**Quick Start with Docker:**
```bash
docker run -d --name redis -p 6379:6379 redis:7
```

---

### 3. **Authentication - Supabase** (REQUIRED)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**Get Free Supabase:**
1. Go to https://supabase.com
2. Create a new project (free tier)
3. Dashboard → Settings → API → Copy the keys

---

### 4. **Database - MongoDB** (REQUIRED)
```bash
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=watchllm
```

**Quick Start with Docker:**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:7
```

---

### 5. **Frontend Environment Variables** (REQUIRED)
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co    # Same as SUPABASE_URL
VITE_SUPABASE_ANON_KEY=your-anon-key                  # Same as SUPABASE_ANON_KEY
```

---

## ⚠️ **IMPORTANT - Should Configure for Production**

### 6. **Admin API Key** (Recommended)
```bash
ADMIN_API_KEY=your-secret-admin-key
```

**Generate with:**
```bash
openssl rand -base64 32
```

---

### 7. **JWT Secret** (Recommended)
```bash
JWT_SECRET=your-very-secure-jwt-secret-change-this
```

**Generate with:**
```bash
openssl rand -base64 32
```

---

## ✅ **OPTIONAL - Can Configure Later**

### 8. **Monitoring - Sentry** (OPTIONAL but Recommended)
```bash
SENTRY_DSN=                        # Leave empty for now
SENTRY_ENVIRONMENT=development
VITE_SENTRY_DSN=                   # Leave empty for now
VITE_SENTRY_ENVIRONMENT=development
```

**Note:** You said you'll configure this later - that's fine! The app will start without it.

---

### 9. **Monitoring - Datadog** (OPTIONAL - Skip for Now)
```bash
DATADOG_ENABLED=false              # Set to false
DATADOG_API_KEY=                   # Leave empty
DD_SERVICE=lynex
DD_ENV=development
DD_VERSION=1.0.0
```

**Note:** As you mentioned, Datadog is overkill for now. Keep it disabled.

---

### 10. **Payments - Whop** (OPTIONAL - Only if Using Whop)
```bash
WHOP_API_KEY=                      # Leave empty if not using
WHOP_WEBHOOK_SECRET=               # Leave empty if not using
```

**Note:** Only needed if you're using Whop for payments/licensing.

---

## 📋 **Quick Start Checklist**

Copy this to your `.env.local` file:

```bash
# =============================================================================
# CRITICAL - REQUIRED FOR APP TO START
# =============================================================================

# Environment
ENV=development
DEBUG=true

# ClickHouse (REQUIRED)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=default

# MongoDB (REQUIRED)
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=watchllm

# Redis (REQUIRED)
REDIS_URL=redis://localhost:6379
QUEUE_MODE=redis

# Supabase (REQUIRED) - Get from https://supabase.com
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR-ANON-KEY
SUPABASE_SERVICE_KEY=YOUR-SERVICE-ROLE-KEY

# JWT Secret (REQUIRED)
JWT_SECRET=GENERATE-WITH-openssl-rand-base64-32

# Admin API Key (REQUIRED)
ADMIN_API_KEY=GENERATE-WITH-openssl-rand-base64-32

# API Configuration
API_HOST=0.0.0.0
INGEST_API_PORT=8001
UI_BACKEND_PORT=8000
BILLING_PORT=8002
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Frontend (REQUIRED)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR-ANON-KEY

# =============================================================================
# OPTIONAL - CAN CONFIGURE LATER
# =============================================================================

# Monitoring - Sentry (OPTIONAL)
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
VITE_SENTRY_DSN=
VITE_SENTRY_ENVIRONMENT=development

# Monitoring - Datadog (DISABLED FOR NOW)
DATADOG_ENABLED=false
DATADOG_API_KEY=
DD_SERVICE=lynex
DD_ENV=development
DD_VERSION=1.0.0

# Payments - Whop (OPTIONAL)
WHOP_API_KEY=
WHOP_WEBHOOK_SECRET=
```

---

## 🐳 **Quick Docker Setup (All Dependencies)**

If you don't have ClickHouse, Redis, and MongoDB running, start them all with Docker:

```bash
# ClickHouse
docker run -d --name clickhouse -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server

# Redis
docker run -d --name redis -p 6379:6379 redis:7

# MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7
```

**Verify they're running:**
```bash
docker ps
```

---

## 🔑 **What You MUST Configure Now**

1. **Supabase** (5 minutes):
   - Go to https://supabase.com
   - Create free project
   - Copy URL, Anon Key, and Service Role Key
   - Paste into `.env.local`

2. **Generate Secrets** (30 seconds):
   ```bash
   # JWT Secret
   openssl rand -base64 32
   
   # Admin API Key
   openssl rand -base64 32
   ```
   - Paste both into `.env.local`

3. **Start Docker Containers** (if not already running):
   ```bash
   docker run -d --name clickhouse -p 8123:8123 -p 9000:9000 clickhouse/clickhouse-server
   docker run -d --name redis -p 6379:6379 redis:7
   docker run -d --name mongodb -p 27017:27017 mongo:7
   ```

---

## ✅ **Summary**

### **MUST CONFIGURE NOW:**
- ✅ ClickHouse (Docker or local)
- ✅ Redis (Docker or local)
- ✅ MongoDB (Docker or local)
- ✅ Supabase (free account)
- ✅ JWT_SECRET (generate)
- ✅ ADMIN_API_KEY (generate)
- ✅ Frontend env vars (VITE_*)

### **CAN SKIP FOR NOW:**
- ⏭️ Sentry (you'll configure later)
- ⏭️ Datadog (overkill, disabled)
- ⏭️ New Relic (not used)
- ⏭️ Whop (only if using payments)

---

## 🚀 **After Configuration**

Once you've set up the required variables, start the services:

```bash
# Backend services
cd services/ingest-api
python main.py

# In another terminal
cd services/processor
python main.py

# In another terminal
cd services/billing
python main.py

# In another terminal
cd services/ui-backend
python main.py

# Frontend
cd web
npm run dev
```

---

**Total Setup Time:** ~10 minutes (mostly waiting for Supabase project creation)

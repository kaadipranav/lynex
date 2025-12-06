# 🗄️ Supabase Setup - SQL Migration

## ✅ What You Need to Do

### Step 1: Open Supabase SQL Editor
1. Go to your Supabase project: **https://app.supabase.com**
2. Click on your project
3. Click **"SQL Editor"** in the left sidebar (database icon)
4. Click **"New Query"**

### Step 2: Run the Schema
1. Open the file: **`supabase_schema.sql`** (I just created it)
2. **Copy ALL the SQL** from that file
3. **Paste it** into the Supabase SQL Editor
4. Click **"Run"** (or press Ctrl+Enter)

### Step 3: Verify It Worked
After running, you should see:
- ✅ "Success. No rows returned"
- Or a list of created tables

Check the **Table Editor** (left sidebar) - you should see:
- `users`
- `projects`
- `project_members`
- `api_keys`

---

## 📋 What the Schema Creates

### Tables:
1. **users** - User profiles (linked to Supabase auth)
2. **projects** - Your projects
3. **project_members** - Team members for each project
4. **api_keys** - API keys for each project

### Security:
- ✅ Row Level Security (RLS) enabled on all tables
- ✅ Users can only see their own data
- ✅ Owners can manage their projects
- ✅ Admins can manage team members

### Automatic Features:
- ✅ Auto-create user profile on signup
- ✅ Auto-update `updated_at` timestamps
- ✅ Proper indexes for performance

---

## ⏭️ After Running the SQL

### Step 1: Get Your Supabase Keys
1. In Supabase, go to **Settings** (gear icon)
2. Click **API**
3. Copy these 3 values:
   - **Project URL** (e.g., `https://abc123.supabase.co`)
   - **anon public** key (click to reveal)
   - **service_role** key (click to reveal - keep this secret!)

### Step 2: Update .env.local
Open your `.env.local` file and update these lines:

```bash
# Replace these 3 lines:
SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# And these 2 frontend lines:
VITE_SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### Step 3: Save and You're Done!
Save `.env.local` and you're ready to start the app!

---

## 🚀 Starting the App

Once `.env.local` is fully configured:

### Backend Services (4 terminals):
```bash
# Terminal 1 - Ingest API
cd services/ingest-api
python main.py

# Terminal 2 - Processor  
cd services/processor
python main.py

# Terminal 3 - UI Backend
cd services/ui-backend
python main.py

# Terminal 4 - Billing
cd services/billing
python main.py
```

### Frontend (1 terminal):
```bash
# Terminal 5 - Frontend
cd web
npm install  # First time only
npm run dev
```

Then open: **http://localhost:5173**

---

## ✅ Checklist

- [ ] Run `supabase_schema.sql` in Supabase SQL Editor
- [ ] Verify tables were created (check Table Editor)
- [ ] Copy Project URL from Supabase
- [ ] Copy anon key from Supabase
- [ ] Copy service_role key from Supabase
- [ ] Update SUPABASE_URL in .env.local
- [ ] Update SUPABASE_ANON_KEY in .env.local
- [ ] Update SUPABASE_SERVICE_KEY in .env.local
- [ ] Update VITE_SUPABASE_URL in .env.local
- [ ] Update VITE_SUPABASE_ANON_KEY in .env.local
- [ ] Save .env.local
- [ ] Start backend services
- [ ] Start frontend
- [ ] Open http://localhost:5173

---

**You're almost there!** Just run the SQL and update the keys! 🚀

# DigitalOcean Deployment Guide

Deploy Lynex to DigitalOcean App Platform using your GitHub Student Pack $200 credit.

## 📊 Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Frontend (React) | Static Site | FREE |
| Ingest API | Basic Service | ~$5 |
| Processor Worker | Basic Service | ~$5 |
| UI Backend | Basic Service | ~$5 |
| Redis | Dev Database | $7 |
| ClickHouse | Droplet (1GB) | $6 |
| **Total** | | **~$28/mo** |

With $200 credit = **7+ months of free hosting!**

---

## 🚀 Quick Start

### Prerequisites

1. **DigitalOcean Account** with Student Pack credit
2. **doctl CLI** installed and authenticated
3. **GitHub repo** pushed to `kaadipranav/sentry-for-ai`

### Step 1: Install doctl CLI

```bash
# macOS
brew install doctl

# Windows
choco install doctl

# Ubuntu
snap install doctl
```

Authenticate:
```bash
doctl auth init
# Enter your API token from: https://cloud.digitalocean.com/account/api/tokens
```

### Step 2: Deploy ClickHouse Droplet

```bash
# Make script executable
chmod +x infra/deploy-clickhouse.sh

# Run deployment
./infra/deploy-clickhouse.sh
```

This will:
- Create a $6/mo droplet
- Install ClickHouse
- Run the schema
- Configure firewall
- Output connection credentials

**Save the credentials!** You'll need them for the App Platform.

### Step 3: Deploy App Platform

```bash
# Create the app
doctl apps create --spec .do/app.yaml

# Get app ID
doctl apps list
```

### Step 4: Configure Secrets

Go to [DigitalOcean Console](https://cloud.digitalocean.com/apps) → Your App → Settings → App-Level Environment Variables

Add these secrets:

| Variable | Value |
|----------|-------|
| `CLICKHOUSE_HOST` | (from Step 2 output) |
| `CLICKHOUSE_PASSWORD` | (from Step 2 output) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `SENTRY_DSN` | Your Sentry DSN |
| `ADMIN_API_KEY` | Generate: `openssl rand -base64 32` |
| `VITE_SUPABASE_URL` | Same as SUPABASE_URL |
| `VITE_SUPABASE_ANON_KEY` | Same as SUPABASE_ANON_KEY |
| `VITE_SENTRY_DSN` | Same as SENTRY_DSN |

### Step 5: Deploy!

```bash
# Trigger deployment
doctl apps create-deployment <app-id>

# Watch logs
doctl apps logs <app-id> --follow
```

---

## 🔧 Manual Configuration

### Update App Spec

After making changes to `app.yaml`:

```bash
doctl apps update <app-id> --spec .do/app.yaml
```

### View Deployment Status

```bash
doctl apps list-deployments <app-id>
```

### SSH to ClickHouse Droplet

```bash
ssh root@<droplet-ip>
clickhouse-client --password <your-password>
```

---

## 🌐 URLs After Deployment

- **Frontend**: `https://<app-name>.ondigitalocean.app`
- **Ingest API**: `https://<app-name>.ondigitalocean.app/ingest`
- **UI Backend**: `https://<app-name>.ondigitalocean.app/api`

---

## 📈 Scaling

When you outgrow the free tier:

### Upgrade Services
Edit `app.yaml` and change `instance_size_slug`:
- `basic-xxs` → `basic-xs` ($10/mo)
- `basic-xs` → `basic-s` ($20/mo)

### Upgrade Redis
Change `size` in databases section:
- `db-s-dev-database` → `db-s-1vcpu-1gb` ($15/mo)

### Upgrade ClickHouse
Create new droplet with more resources:
- `s-1vcpu-2gb` ($12/mo)
- `s-2vcpu-4gb` ($24/mo)

---

## 🔒 Security Checklist

- [ ] Set strong `ADMIN_API_KEY`
- [ ] Configure ClickHouse firewall to App Platform IPs only
- [ ] Enable Supabase Row Level Security
- [ ] Set `DEBUG=false` in production
- [ ] Configure CORS_ORIGINS properly

---

## 🐛 Troubleshooting

### App won't deploy
```bash
doctl apps logs <app-id> --type=build
```

### Service unhealthy
```bash
doctl apps logs <app-id> --component=<service-name>
```

### ClickHouse connection failed
1. Check firewall rules: `doctl compute firewall list`
2. Test connection: `nc -zv <droplet-ip> 9000`
3. Check ClickHouse logs: `ssh root@<ip> journalctl -u clickhouse-server`

### Redis connection failed
1. Check DATABASE_URL is set
2. Verify Redis is running in App Platform dashboard

---

## 📚 Resources

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [doctl CLI Reference](https://docs.digitalocean.com/reference/doctl/)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [GitHub Student Pack](https://education.github.com/pack)

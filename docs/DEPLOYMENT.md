# Deployment Guide - DigitalOcean

## Prerequisites

- DigitalOcean account with $200 student credit
- GitHub repository with code
- Domain name (lynex.dev)
- Sentry account with DSN
- Datadog account with API key (optional)

## Option 1: DigitalOcean App Platform (Recommended)

### Advantages
- Automatic scaling
- Built-in SSL
- Easy rollbacks
- Managed databases available
- Zero-downtime deployments

### Steps

1. **Connect GitHub Repository**
   - Go to https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Select "GitHub" as source
   - Authorize DigitalOcean
   - Select your repository

2. **Configure Services**
   
   **Ingest API:**
   - Type: Web Service
   - Source Directory: `/services/ingest-api`
   - Build Command: (auto-detected)
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port 8000`
   - HTTP Port: 8000
   - Instance Size: Basic ($12/month)
   
   **UI Backend:**
   - Type: Web Service
   - Source Directory: `/services/ui-backend`
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port 8001`
   - HTTP Port: 8001
   - Instance Size: Basic ($12/month)
   
   **Processor:**
   - Type: Worker
   - Source Directory: `/services/processor`
   - Run Command: `python main.py`
   - Instance Size: Basic ($12/month)
   
   **Frontend:**
   - Type: Static Site
   - Source Directory: `/web`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Add Managed Databases**
   - Add Redis (Managed Database) - $15/month
   - Add PostgreSQL for metadata (optional) - $15/month
   - For ClickHouse: Use Aiven or self-hosted droplet

4. **Configure Environment Variables**
   ```
   REDIS_URL=${redis.DATABASE_URL}
   CLICKHOUSE_HOST=your-clickhouse-host
   CLICKHOUSE_PASSWORD=your-password
   SENTRY_DSN=your-sentry-dsn
   ENV=production
   DATADOG_ENABLED=true
   DATADOG_API_KEY=your-datadog-key
   ```

5. **Deploy**
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)
   - App Platform will provide URLs

6. **Configure Custom Domain**
   - Go to Settings → Domains
   - Add `api.lynex.dev` → Ingest API
   - Add `app.lynex.dev` → Frontend
   - Update DNS records at your domain registrar

## Option 2: DigitalOcean Droplet (More Control)

### Advantages
- Full control
- Lower cost ($12/month for all services)
- Can run ClickHouse locally

### Steps

1. **Create Droplet**
   - Go to https://cloud.digitalocean.com/droplets
   - Create Droplet
   - Choose: Ubuntu 22.04 LTS
   - Size: Basic - $24/month (4GB RAM, 2 vCPUs)
   - Add SSH key
   - Create

2. **SSH into Droplet**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

4. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

5. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/lynex.git
   cd lynex
   ```

6. **Create Production .env**
   ```bash
   nano .env
   ```
   
   Add:
   ```
   REDIS_URL=redis://localhost:6379
   CLICKHOUSE_HOST=localhost
   CLICKHOUSE_PASSWORD=your-secure-password
   SENTRY_DSN=your-sentry-dsn
   ENV=production
   DATADOG_ENABLED=true
   DATADOG_API_KEY=your-datadog-key
   ```

7. **Start Services**
   ```bash
   docker-compose up -d
   ```

8. **Install Nginx for Reverse Proxy**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

9. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/lynex
   ```
   
   Add configuration (see nginx config below)

10. **Enable Site**
    ```bash
    sudo ln -s /etc/nginx/sites-available/lynex /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. **Get SSL Certificate**
    ```bash
    sudo certbot --nginx -d api.lynex.dev -d app.lynex.dev
    ```

12. **Install Datadog Agent**
    ```bash
    DD_API_KEY=your-key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"
    ```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/lynex

# API Backend
server {
    listen 80;
    server_name api.lynex.dev;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name app.lynex.dev;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Frontend Deployment to Vercel (Recommended)

1. **Sign up at Vercel**
   - Go to https://vercel.com
   - Sign up with GitHub

2. **Import Project**
   - Click "New Project"
   - Import your GitHub repository
   - Root Directory: `web/`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Environment Variables**
   ```
   VITE_API_URL=https://api.lynex.dev
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build (2-3 minutes)

5. **Custom Domain**
   - Go to Settings → Domains
   - Add `app.lynex.dev`
   - Update DNS records

## Cost Estimate

### App Platform
- 3 Web Services: $36/month
- 1 Worker: $12/month
- Managed Redis: $15/month
- **Total: ~$63/month** (covered by $200 credit for 3+ months)

### Droplet + Vercel
- 1 Droplet (4GB): $24/month
- Vercel: $0 (free tier)
- **Total: $24/month** (covered by $200 credit for 8+ months)

## Monitoring Setup

After deployment:

1. **Sentry**
   - Verify errors are being tracked
   - Set up alerts for critical errors

2. **Datadog**
   - Check APM dashboard for traces
   - Set up monitors for:
     - High error rate (>5%)
     - High latency (>1s p95)
     - Low throughput (<10 req/min)
   - Create dashboard with key metrics

3. **Uptime Monitoring**
   - Use UptimeRobot (free) or Datadog Synthetics
   - Monitor: api.lynex.dev/health
   - Alert on downtime

## Rollback Procedure

### App Platform
- Go to app settings
- Click "Rollback" to previous deployment

### Droplet
```bash
cd lynex
git checkout previous-commit
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Services won't start
- Check logs: `docker-compose logs [service]`
- Verify environment variables
- Check database connections

### High memory usage
- Reduce worker count
- Enable swap: `sudo fallocate -l 2G /swapfile`

### SSL certificate issues
- Renew: `sudo certbot renew`
- Check nginx config: `sudo nginx -t`

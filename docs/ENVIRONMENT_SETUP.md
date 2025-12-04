# Environment Configuration Guide

This document describes how to configure and validate environment variables across all Lynex services.

## Quick Start

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Fill in your values
# Edit .env with your actual configuration

# 3. Validate the configuration
bash scripts/setup-env.sh validate

# 4. Test connections
bash scripts/setup-env.sh test
```

## Environment Files Structure

```
config/
├── environments/
│   ├── development.env    # Local development settings
│   ├── staging.env        # Staging environment
│   └── production.env     # Production settings
```

### Using Environment-Specific Configs

```bash
# Development
cp config/environments/development.env .env

# Staging
cp config/environments/staging.env .env
# Then fill in actual staging credentials

# Production
cp config/environments/production.env .env
# Then fill in actual production credentials
```

## Required Variables by Service

### All Services
| Variable | Description | Required |
|----------|-------------|----------|
| `ENV` | Environment (development/staging/production) | Yes |
| `DEBUG` | Enable debug mode | Yes |
| `SENTRY_DSN` | Sentry error tracking | No (recommended) |

### Ingest API (Port 8000)
| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_URL` | Redis connection URL | Yes |
| `CLICKHOUSE_HOST` | ClickHouse server host | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `QUEUE_MODE` | redis or memory | No (default: redis) |

### UI Backend (Port 8001)
| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_URL` | Redis connection URL | Yes |
| `CLICKHOUSE_HOST` | ClickHouse server host | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes |
| `JWT_SECRET` | JWT signing secret | Yes |

### Processor Worker
| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_URL` | Redis connection URL | Yes |
| `CLICKHOUSE_HOST` | ClickHouse server host | Yes |
| `SLACK_WEBHOOK_URL` | Slack alerts webhook | No |

### Billing Service (Port 8002)
| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_URL` | Redis connection URL | Yes |
| `WHOP_API_KEY` | Whop API key | No (if not using payments) |
| `WHOP_WEBHOOK_SECRET` | Whop webhook secret | No |

## Configuration Validation

All services use the shared validation module (`services/shared/config.py`) which:

1. **Validates required variables** on startup
2. **Warns about missing optional variables**
3. **Displays environment information** in logs
4. **Fails fast** if critical config is missing

### Example Startup Output

```
============================================================
[UI-Backend] Configuration Validation
============================================================
Environment: development
Debug Mode: True
------------------------------------------------------------
✓ Required: REDIS_URL
✓ Required: CLICKHOUSE_HOST
✓ Required: SUPABASE_URL
✓ Required: SUPABASE_ANON_KEY
------------------------------------------------------------
⚠ Optional (not set): SENTRY_DSN
============================================================
```

## Validation Script

The `scripts/setup-env.sh` script provides several commands:

```bash
# Validate all required variables are set
bash scripts/setup-env.sh validate

# Test connections to external services
bash scripts/setup-env.sh test

# Show current environment values (masked)
bash scripts/setup-env.sh show

# Generate a new .env from template
bash scripts/setup-env.sh init
```

## ClickHouse Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLICKHOUSE_HOST` | localhost | Server hostname |
| `CLICKHOUSE_PORT` | 8123 | HTTP port |
| `CLICKHOUSE_USER` | default | Username |
| `CLICKHOUSE_PASSWORD` | (empty) | Password |
| `CLICKHOUSE_DATABASE` | default | Database name |
| `CLICKHOUSE_SECURE` | false | Use HTTPS |

## Redis Configuration

The `REDIS_URL` format:
```
redis://[:password@]host:port[/db]

# Examples:
redis://localhost:6379          # Local
redis://:mypass@localhost:6379  # With password
rediss://user:pass@host:6380    # TLS (Upstash)
```

## Supabase Configuration

Get these from your Supabase dashboard (Settings → API):

| Variable | Where to Find |
|----------|---------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | anon / public key |
| `SUPABASE_SERVICE_KEY` | service_role key (keep secret!) |
| `JWT_SECRET` | Settings → API → JWT Secret |

## Datadog APM (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATADOG_ENABLED` | false | Enable APM |
| `DD_SERVICE` | lynex-{service} | Service name |
| `DD_ENV` | development | Environment tag |
| `DD_VERSION` | 1.0.0 | Version tag |
| `DD_AGENT_HOST` | localhost | Agent hostname |

## Environment-Specific Notes

### Development
- Use `localhost` for all services
- Enable `DEBUG=true`
- Can use memory queue mode for quick testing

### Staging
- Use staging database instances
- Enable Sentry tracking
- Test with production-like configuration

### Production
- `DEBUG=false` always
- Enable all monitoring (Sentry, optional Datadog)
- Use secure connections (HTTPS, TLS)
- Never commit production credentials

## Security Best Practices

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use secrets management** - GitHub Secrets, DO App Spec envs
3. **Rotate credentials regularly** - Especially JWT_SECRET
4. **Use read-only keys where possible** - Supabase anon key
5. **Enable monitoring** - Sentry catches config issues early

## Troubleshooting

### "Missing required variable: X"
Run `bash scripts/setup-env.sh validate` to see all missing variables.

### "Connection refused to Redis/ClickHouse"
1. Check the service is running
2. Verify the URL/host is correct
3. Check firewall rules
4. Run `bash scripts/setup-env.sh test`

### "Invalid Supabase JWT"
1. Verify `SUPABASE_URL` is correct (no trailing slash)
2. Check `SUPABASE_ANON_KEY` is the full key
3. Ensure `JWT_SECRET` matches your Supabase project

### Environment not loading
1. Check `.env` file exists in project root
2. Verify file has Unix line endings (LF, not CRLF)
3. No spaces around `=` in variable assignments

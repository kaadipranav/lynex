# GitHub Actions CI/CD Documentation

This repository uses GitHub Actions for continuous integration and deployment. All workflows are free for public repositories, and private repos get 2,000 minutes/month free.

## 📁 Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | Pull Requests, Push to main | Run tests, linting, type checking |
| `deploy.yml` | Push to main | Deploy to DigitalOcean App Platform |
| `sdk-publish.yml` | Version tags (v*) | Publish SDKs to PyPI and npm |

---

## 🔐 Required Secrets

Configure these secrets in **Settings → Secrets and variables → Actions**:

### DigitalOcean Deployment

| Secret | Description | How to Get |
|--------|-------------|------------|
| `DIGITALOCEAN_ACCESS_TOKEN` | DO API token for deployments | [DO Console → API → Tokens](https://cloud.digitalocean.com/account/api/tokens) |
| `CLICKHOUSE_HOST` | ClickHouse droplet IP | From `deploy-clickhouse.sh` output |
| `CLICKHOUSE_PASSWORD` | ClickHouse password | From `deploy-clickhouse.sh` output |

### Supabase Auth

| Secret | Description | How to Get |
|--------|-------------|------------|
| `SUPABASE_URL` | Project URL | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Anonymous key (public) | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Service role key (secret) | Supabase Dashboard → Settings → API |
| `VITE_SUPABASE_URL` | Same as SUPABASE_URL | - |
| `VITE_SUPABASE_ANON_KEY` | Same as SUPABASE_ANON_KEY | - |

### Monitoring

| Secret | Description | How to Get |
|--------|-------------|------------|
| `SENTRY_DSN` | Sentry project DSN | [Sentry → Project → Settings → Client Keys](https://sentry.io) |
| `VITE_SENTRY_DSN` | Same DSN for frontend | - |

### Frontend

| Secret | Description | How to Get |
|--------|-------------|------------|
| `VITE_API_URL` | Backend API URL | After first deploy, use App Platform URL |

### SDK Publishing

| Secret | Description | How to Get |
|--------|-------------|------------|
| `PYPI_API_TOKEN` | PyPI API token | [PyPI → Account → API tokens](https://pypi.org/manage/account/) |
| `NPM_TOKEN` | npm automation token | [npmjs.com → Access Tokens](https://www.npmjs.com/settings/~/tokens) |

### Optional

| Secret | Description | How to Get |
|--------|-------------|------------|
| `ADMIN_API_KEY` | Admin API key for tier upgrades | Generate: `openssl rand -base64 32` |
| `SLACK_WEBHOOK_URL` | Slack notifications (optional) | Slack App → Incoming Webhooks |

---

## 🚀 Quick Setup

### 1. Fork/Clone Repository

```bash
git clone https://github.com/kaadipranav/sentry-for-ai.git
cd sentry-for-ai
```

### 2. Add Required Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Minimum required secrets for deployment:
- `DIGITALOCEAN_ACCESS_TOKEN`
- `CLICKHOUSE_HOST`
- `CLICKHOUSE_PASSWORD`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

### 3. Enable Actions

Go to **Actions** tab → Click **"I understand my workflows, go ahead and enable them"**

### 4. Push to Main

```bash
git push origin main
```

The deploy workflow will automatically:
1. Build and test all services
2. Deploy to DigitalOcean App Platform
3. Run smoke tests
4. Notify on success/failure

---

## 📦 Publishing SDKs

### Automatic (Recommended)

Create a version tag to trigger automatic publishing:

```bash
# Update version in setup.py and package.json first
git tag v1.0.0
git push origin v1.0.0
```

### Manual

Go to **Actions** → **Publish SDKs** → **Run workflow**

Enter the version number and select which SDKs to publish.

---

## 🧪 Test Workflow

The test workflow runs automatically on:
- Every pull request to `main`
- Every push to `main`

It runs:
- Python service tests (pytest)
- Python SDK tests
- JS SDK tests (npm test)
- Frontend build test
- Linting (ruff, eslint)
- Type checking (mypy, tsc)

---

## 🔧 Environment Configuration

### Production Environment

Create a GitHub Environment named `production` in **Settings → Environments**.

Add environment-specific secrets and protection rules:
- Required reviewers
- Wait timer
- Deployment branches (main only)

### Environment Variables

The workflows automatically set these based on secrets:
- `ENV=production`
- `DEBUG=false`
- `SENTRY_ENVIRONMENT=production`

---

## 🐛 Troubleshooting

### Workflow Not Running

1. Check if Actions are enabled (Actions tab)
2. Verify branch protection rules
3. Check workflow file syntax

### Deployment Failing

1. Verify `DIGITALOCEAN_ACCESS_TOKEN` is valid
2. Check if app exists: `doctl apps list`
3. Review deployment logs in DO Console

### SDK Publish Failing

1. Verify `PYPI_API_TOKEN` / `NPM_TOKEN` are valid
2. Check if version already exists
3. Ensure package builds locally first

### Tests Failing

1. Review test output in Actions tab
2. Run tests locally: `pytest -v`
3. Check if dependencies are installed

---

## 📊 Workflow Costs

| Workflow | Avg. Runtime | Monthly Usage (10 deploys) |
|----------|--------------|---------------------------|
| test.yml | ~3 min | ~30 min |
| deploy.yml | ~5 min | ~50 min |
| sdk-publish.yml | ~3 min | ~6 min (2 releases) |
| **Total** | | **~90 min/month** |

Free tier: 2,000 min/month (private) or unlimited (public)

---

## 🔗 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [DigitalOcean doctl Reference](https://docs.digitalocean.com/reference/doctl/)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [npm Publishing Guide](https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry)

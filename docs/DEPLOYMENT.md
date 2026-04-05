# ShieldPay Deployment Guide

## Architecture Overview

```
                    ┌──────────────┐
                    │   Vercel      │
                    │  (Frontend)   │
                    │  Next.js 14   │
                    └──────┬───────┘
                           │ HTTPS
                           ▼
                    ┌──────────────┐         ┌──────────────┐
                    │   Railway     │────────▶│  PostgreSQL   │
                    │  (Backend)    │         │  (Railway)    │
                    │  FastAPI      │         └──────────────┘
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │    Stripe     │
                    │  (Payments)   │
                    └──────────────┘
```

## Prerequisites

- GitHub repository with the ShieldPay monorepo
- Stripe account with Connect enabled
- Domain name (optional but recommended)

## 1. Database (Railway PostgreSQL)

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Create project and provision Postgres
railway init
railway add --plugin postgresql

# Get the connection URL
railway variables | grep DATABASE_URL
```

Alternatively, use **Neon** (free tier) or **Supabase** for PostgreSQL.

## 2. Backend (Railway)

### Environment Variables

Set these in Railway dashboard or via CLI:

```bash
railway variables set DATABASE_URL="postgresql+asyncpg://..."
railway variables set STRIPE_SECRET_KEY="sk_live_..."
railway variables set STRIPE_WEBHOOK_SECRET="whsec_..."
railway variables set STRIPE_PUBLISHABLE_KEY="pk_live_..."
railway variables set JWT_SECRET="<random-64-char-string>"
railway variables set JWT_ALGORITHM="HS256"
railway variables set JWT_EXPIRY_HOURS="24"
railway variables set FRONTEND_URL="https://shieldpay.io"
railway variables set SENDGRID_API_KEY="SG..."
railway variables set SENTRY_DSN="https://...@sentry.io/..."
```

### Deploy

Railway auto-deploys from GitHub. Add a `Procfile` to `backend/`:

```
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or use the Railway Dockerfile builder with `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
RUN alembic upgrade head
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Run Migrations

```bash
railway run alembic upgrade head
```

## 3. Frontend (Vercel)

### Setup

1. Import the GitHub repo in Vercel
2. Set root directory to `frontend`
3. Framework preset: Next.js

### Environment Variables

```
NEXT_PUBLIC_API_URL=https://api.shieldpay.io
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXTAUTH_URL=https://shieldpay.io
NEXTAUTH_SECRET=<random-string>
```

### Custom Domain

1. Add your domain in Vercel project settings
2. Update DNS records as instructed
3. SSL is automatic

## 4. Stripe Configuration

### Webhook Endpoint

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://api.shieldpay.io/api/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `transfer.created`
   - `account.updated`
   - `charge.dispute.created`
   - `charge.refunded`
4. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`

### Connect Settings

1. Enable Stripe Connect in dashboard
2. Set redirect URIs for onboarding
3. Configure branding (logo, colors)

## 5. Post-Deployment Checklist

- [ ] Run `alembic upgrade head` on production database
- [ ] Verify health endpoint: `curl https://api.shieldpay.io/health`
- [ ] Test Stripe webhook: `stripe trigger payment_intent.succeeded`
- [ ] Test Connect onboarding flow end-to-end
- [ ] Verify CORS only allows production frontend URL
- [ ] Verify rate limiting is active (`RATE_LIMIT_ENABLED` is not `false`)
- [ ] Check Sentry receives error events
- [ ] Run `bandit -r backend/app/` for Python security scan
- [ ] Run `cd frontend && npm audit` for Node security scan
- [ ] Set up UptimeRobot monitoring for `/health`
- [ ] Configure custom domain and verify SSL

## 6. Monitoring

### Error Tracking (Sentry)

- Backend: automatic via `sentry-sdk[fastapi]`
- Set `SENTRY_DSN` environment variable
- Free tier: 5,000 events/month

### Uptime Monitoring

- UptimeRobot (free): monitor `GET /health` every 5 minutes
- Alert via email/Slack on downtime

### Logs

- Railway: built-in log viewer
- Vercel: built-in function logs

## 7. Cost Estimate

| Service | Plan | Monthly Cost |
|---------|------|-------------|
| Vercel | Hobby (free) | $0 |
| Railway | Starter | $5-15 |
| PostgreSQL | Railway addon | Included |
| Stripe | Pay-as-you-go | 2.9% + $0.30/txn |
| SendGrid | Free tier | $0 (100 emails/day) |
| Sentry | Free tier | $0 (5K events/month) |
| Domain | .io | ~$30/year |
| **Total** | | **~$10-20/month** |

## 8. Scaling

When traffic grows:

1. **Database**: Upgrade Railway Postgres plan or migrate to RDS
2. **Backend**: Railway auto-scales with plan upgrade
3. **Frontend**: Vercel scales automatically on all plans
4. **Cache**: Add Redis for rate limiting and session storage
5. **Background Jobs**: Add Celery/ARQ for async processing (auto-release, emails)

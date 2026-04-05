# ShieldPay — Production Setup Guide

Follow these steps to get real API keys for all services.

---

## 1. Stripe (Payments)

Stripe handles all payment processing, escrow, and freelancer payouts.

### Sign up
1. Go to **https://dashboard.stripe.com/register**
2. Create an account and verify your email

### Get test API keys
1. Go to **https://dashboard.stripe.com/test/apikeys**
2. Copy **Publishable key** (`pk_test_...`) → put in both:
   - `backend/.env` → `STRIPE_PUBLISHABLE_KEY`
   - `frontend/.env.local` → `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
3. Copy **Secret key** (`sk_test_...`) →
   - `backend/.env` → `STRIPE_SECRET_KEY`

### Enable Stripe Connect (required for freelancer payouts)
1. Go to **https://dashboard.stripe.com/test/connect/accounts/overview**
2. Click **Get started** and complete the Connect setup
3. Set platform type to **Express**

### Set up webhook (local development)
```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli#install
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to your local backend
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```
4. Copy the `whsec_...` secret it prints →
   - `backend/.env` → `STRIPE_WEBHOOK_SECRET`

### Set up webhook (production)
1. Go to **https://dashboard.stripe.com/test/webhooks** (or live mode)
2. Click **Add endpoint**
3. URL: `https://YOUR_BACKEND_URL/api/webhooks/stripe`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `transfer.created`
   - `account.updated`
   - `charge.dispute.created`
   - `charge.refunded`
5. Copy the signing secret → `STRIPE_WEBHOOK_SECRET`

---

## 2. JWT Secret (Authentication)

Already generated in your `.env`. If you need a new one:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Put the output in `backend/.env` → `JWT_SECRET`

**Important:** Use a DIFFERENT secret for production vs development.

---

## 3. SendGrid (Emails)

Sends payment link emails, milestone notifications, and dispute alerts.

### Sign up
1. Go to **https://signup.sendgrid.com/**
2. Create a free account (100 emails/day free)
3. Complete email verification

### Get API key
1. Go to **https://app.sendgrid.com/settings/api_keys**
2. Click **Create API Key**
3. Name: `ShieldPay`
4. Permissions: **Full Access** (or Restricted → Mail Send only)
5. Copy the key (`SG...`) →
   - `backend/.env` → `SENDGRID_API_KEY`

### Verify sender
1. Go to **https://app.sendgrid.com/settings/sender_auth**
2. Verify the email/domain you'll send from
3. Update `FROM_EMAIL` in `backend/app/services/notification_service.py` if needed

> **Note:** Without SendGrid configured, emails are logged to the console instead. The app works fine without it.

---

## 4. Sentry (Error Monitoring)

Tracks backend errors and performance in production.

### Sign up
1. Go to **https://sentry.io/signup/**
2. Create a free account (5,000 events/month free)

### Create project
1. Click **Create Project**
2. Platform: **Python** → **FastAPI**
3. Copy the DSN (`https://...@sentry.io/...`) →
   - `backend/.env` → `SENTRY_DSN`

> **Note:** Without Sentry configured, errors are logged locally. The app works fine without it.

---

## 5. Railway (Backend Hosting)

Hosts the FastAPI backend and PostgreSQL database.

### Sign up & deploy
1. Go to **https://railway.app/** and sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your ShieldPay repo
4. Set **Root Directory** to `backend`

### Add PostgreSQL
1. In your Railway project, click **+ New** → **Database** → **PostgreSQL**
2. Railway auto-provides `DATABASE_URL`
3. **Important:** Change the scheme from `postgresql://` to `postgresql+asyncpg://`:
   - Go to Variables → edit `DATABASE_URL`
   - Replace `postgresql://` with `postgresql+asyncpg://`

### Set environment variables
In Railway dashboard → your service → **Variables**, add ALL of these:

```
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://... (auto-provided, just fix prefix)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
JWT_SECRET=<your-production-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
FRONTEND_URL=https://your-frontend.vercel.app
SENDGRID_API_KEY=SG...
SENTRY_DSN=https://...@sentry.io/...
```

### Custom domain (optional)
1. Go to Settings → Networking → Custom Domain
2. Add your domain (e.g., `api.shieldpay.io`)
3. Update DNS as instructed

---

## 6. Vercel (Frontend Hosting)

Hosts the Next.js frontend with automatic SSL and CDN.

### Sign up & deploy
1. Go to **https://vercel.com/signup** and sign up with GitHub
2. Click **Import Project** → select your ShieldPay repo
3. Set **Root Directory** to `frontend`
4. Framework: **Next.js** (auto-detected)

### Set environment variables
In Vercel dashboard → your project → **Settings** → **Environment Variables**:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
NEXTAUTH_URL=https://your-frontend.vercel.app
NEXTAUTH_SECRET=<your-production-secret>
```

### Custom domain (optional)
1. Go to Settings → Domains
2. Add your domain (e.g., `shieldpay.io`)
3. Update DNS as instructed

---

## 7. Post-Setup Verification

After configuring all services, verify everything works:

```bash
# 1. Health check
curl https://YOUR_BACKEND_URL/health
# Should return: {"status":"ok","environment":"production","database":"connected"}

# 2. Test Stripe webhook
stripe trigger payment_intent.succeeded --api-key sk_test_...

# 3. Test registration
curl -X POST https://YOUR_BACKEND_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","full_name":"Test","role":"freelancer"}'

# 4. Open frontend
open https://YOUR_FRONTEND_URL
```

---

## Quick Reference: Where Each Key Goes

| Key | Backend `.env` | Frontend `.env.local` | Vercel | Railway |
|-----|---------------|----------------------|--------|---------|
| `STRIPE_SECRET_KEY` | Yes | - | - | Yes |
| `STRIPE_PUBLISHABLE_KEY` | Yes | Yes (`NEXT_PUBLIC_`) | Yes | Yes |
| `STRIPE_WEBHOOK_SECRET` | Yes | - | - | Yes |
| `JWT_SECRET` | Yes | - | - | Yes |
| `SENDGRID_API_KEY` | Yes | - | - | Yes |
| `SENTRY_DSN` | Yes | - | - | Yes |
| `DATABASE_URL` | Yes | - | - | Auto |
| `FRONTEND_URL` | Yes | - | - | Yes |
| `NEXT_PUBLIC_API_URL` | - | Yes | Yes | - |
| `NEXTAUTH_SECRET` | - | Yes | Yes | - |

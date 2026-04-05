# ShieldPay

Freelancer Payment Protection Platform — escrow-based payments that protect both freelancers and clients.

## Architecture

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS 3.4
- **Payments**: Stripe Connect (Payment Intents, Webhooks, Connect Payouts)
- **Auth**: NextAuth.js v5 (frontend) + JWT validation (backend)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 18+

### 1. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL on port 5432 and Redis on port 6379.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in your values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API available at http://localhost:8000 — docs at http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # then fill in your values
npm run dev
```

App available at http://localhost:3000

## Project Structure

```
shieldpay/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── utils/    # Helpers
│   └── tests/
├── frontend/         # Next.js application
│   └── src/
│       ├── app/      # App Router pages
│       ├── components/
│       ├── lib/      # API client, utilities
│       └── hooks/
└── docs/
```

## Stripe Webhooks

ShieldPay relies on Stripe webhooks to process payments, fund milestones, and handle disputes. In local development, use the Stripe CLI to forward events:

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login

# Forward webhooks to your local backend
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Copy the webhook signing secret (whsec_...) and add to backend/.env:
# STRIPE_WEBHOOK_SECRET=whsec_...
```

### Handled Events

| Event | Action |
|-------|--------|
| `payment_intent.succeeded` | Funds milestone, activates project, notifies freelancer |
| `payment_intent.payment_failed` | Marks payment failed, notifies client |
| `transfer.created` | Logs transfer, notifies freelancer of payout |
| `account.updated` | Updates freelancer verification status |
| `charge.dispute.created` | Creates dispute record, freezes milestone, notifies both parties |
| `charge.refunded` | Updates payment/milestone to refunded status |

All events are idempotent — duplicate event IDs are safely ignored via the `webhook_events` table.

### Testing Webhooks

```bash
# Trigger a test event
stripe trigger payment_intent.succeeded

# Run webhook tests
cd backend && python -m pytest tests/test_webhooks.py -v
```

## Conventions

- All money stored as **integer cents** (never floats)
- All dates stored as **UTC timestamps**
- Python: `snake_case`, type hints everywhere, async/await for all I/O
- TypeScript: `camelCase`, strict mode, no `any`
- Git commits follow [Conventional Commits](https://www.conventionalcommits.org/)

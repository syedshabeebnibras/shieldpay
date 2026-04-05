# ShieldPay Architecture

## Overview

ShieldPay is an escrow-based payment platform for freelancers. Clients fund milestones, freelancers deliver work, and payments are released upon approval.

## System Flow

```
Client creates project → Defines milestones → Funds milestone (Stripe)
    → Payment held in escrow → Freelancer delivers work
    → Client approves → Payment released to freelancer (Stripe Connect)
```

## Stack

| Layer      | Technology                          |
| ---------- | ----------------------------------- |
| Frontend   | Next.js 14, TypeScript, Tailwind    |
| Backend    | FastAPI, SQLAlchemy 2.0, Pydantic   |
| Database   | PostgreSQL 16 (async via asyncpg)   |
| Payments   | Stripe Connect                      |
| Auth       | NextAuth.js v5 + JWT                |
| Cache      | Redis 7                             |

## Backend Architecture

```
app/
├── api/         # Route handlers (thin controllers)
├── models/      # SQLAlchemy ORM models
├── schemas/     # Pydantic request/response schemas
├── services/    # Business logic layer
└── utils/       # Cross-cutting concerns (auth, errors)
```

- **Controllers** (api/) handle HTTP concerns only
- **Services** contain all business logic
- **Models** define database schema
- **Schemas** validate input/output

## Payment Flow

1. Client creates a PaymentIntent via Stripe
2. Funds are captured and held (not transferred)
3. On milestone approval, a Transfer is created to the freelancer's Connected Account
4. Stripe webhooks confirm payment status changes

## Security

- JWT authentication on all protected endpoints
- Stripe webhook signature verification
- Rate limiting via slowapi
- CORS restricted to frontend origin
- All money as integer cents (no floating point)

# ShieldPay API Documentation

Base URL: `http://localhost:8000`

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Health
- `GET /health` — Health check

### Auth
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Login and receive JWT

### Users
- `GET /api/users/me` — Get current user profile
- `PATCH /api/users/me` — Update profile

### Projects
- `GET /api/projects` — List projects
- `POST /api/projects` — Create project
- `GET /api/projects/{id}` — Get project detail
- `PATCH /api/projects/{id}` — Update project

### Milestones
- `GET /api/projects/{id}/milestones` — List milestones for project
- `POST /api/projects/{id}/milestones` — Create milestone
- `PATCH /api/milestones/{id}` — Update milestone status

### Payments
- `POST /api/payments/create-intent` — Create Stripe PaymentIntent
- `GET /api/payments/{id}` — Get payment status

### Webhooks
- `POST /api/webhooks/stripe` — Stripe webhook handler

### Disputes
- `POST /api/disputes` — Open a dispute
- `GET /api/disputes/{id}` — Get dispute detail
- `PATCH /api/disputes/{id}` — Update dispute status

### Ratings
- `POST /api/ratings` — Submit a rating
- `GET /api/users/{id}/ratings` — Get ratings for a user

# Pulseboard Analytics

Production-style monorepo for the PDF must-have scope: multi-tenant auth, API key ingestion, CSV upload, async event normalization, dashboard widgets, sharing, and auto-refresh.

## Stack

- Backend: FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2, Celery, Redis, PostgreSQL.
- Frontend: Next.js App Router, TypeScript, Tailwind, TanStack Query, Zustand, Recharts, react-grid-layout.
- Runtime: Docker Compose with `api`, `web`, `postgres`, `redis`, and `celery-worker`.

## Local Setup

1. Start Docker Desktop.
2. Copy `.env.example` to `.env` if you want to customize secrets.
3. Run:

```bash
docker compose up --build
```

4. Seed local data:

```bash
docker compose exec api python -m scripts.seed
```

5. Open:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

The browser-facing frontend uses the same-origin `/api/backend` proxy. The Next.js server forwards those requests to `API_INTERNAL_URL`, which defaults to the Compose service URL `http://api:8000/api/v1`.

Seed login:

- Email: `owner@example.com`
- Password: `Password123!`

## Architecture

The API follows a layered design:

- Routers handle HTTP shape and dependencies.
- Services own business rules and transactions.
- Repositories enforce tenant-scoped persistence access.
- Models define relational boundaries and indexes.
- Custom exceptions return a consistent error envelope with request IDs.

Ingestion accepts single events, batches, and CSV uploads through API-key auth. Raw events are persisted first, then Celery normalizes them into the queryable `events` table. Dashboard widgets use a safe query-builder contract rather than raw SQL.

## Tests

Backend integration tests:

```bash
docker compose exec api pytest
```

The test suite uses `TEST_DATABASE_URL` and creates `analytics_test` automatically, so it does not wipe the local application database.

Frontend component tests:

```bash
docker compose exec web npm test
```

Frontend E2E tests:

```bash
docker compose exec web npx playwright install chromium
docker compose exec web npm run test:e2e
```

## Public Deployment

Use [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the public stack:

- Vercel for `apps/web`
- Render for API and Celery worker
- Neon for PostgreSQL
- Upstash Redis or another Redis-compatible provider for Celery/rate limiting

## API Guide

Use [docs/API_GUIDE.md](docs/API_GUIDE.md) for shareable API documentation with endpoint summaries, request/response examples, auth details, roles, errors, ingestion, dashboards, and public sharing.

## Must-Have Coverage

- JWT auth with refresh cookie.
- Signup creates an organization and Owner membership.
- Owner/Admin/Analyst/Viewer roles with endpoint guards.
- Invite creation with dev outbox token visibility.
- API key generation, rotation, revocation, hashed storage.
- Single event, batch event, and CSV ingestion.
- Async normalization via Celery.
- Custom dashboards and widgets: line, bar, pie, KPI, table.
- Safe query builder with time bucketing, filters, and grouping.
- Team-only dashboards and public read-only share links.
- Auto-refreshing dashboard widget data.

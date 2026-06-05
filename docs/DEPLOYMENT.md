# Public Deployment Guide

This guide deploys the app with:

- Frontend: Vercel, project root `apps/web`
- API and Celery worker: Render, from `render.yaml`
- PostgreSQL: Neon
- Redis: Upstash Redis or another Redis provider with a `redis://` or `rediss://` URL

## 1. Create Neon Postgres

Create a Neon project and copy the connection string from the dashboard.

Use the direct connection string for the API:

```text
postgresql://USER:PASSWORD@HOST.neon.tech/DB?sslmode=require
```

The app normalizes `postgresql://` to SQLAlchemy's async driver automatically.

## 2. Create Redis

Create an Upstash Redis database and copy the Redis TLS URL.

For Celery, Upstash documents this URL format:

```text
rediss://:PASSWORD@HOST:PORT?ssl_cert_reqs=required
```

Use the same URL for:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## 3. Deploy API And Worker On Render

1. Push this repo to GitHub.
2. In Render, create a Blueprint from the repo root.
3. Render will read `render.yaml` and create:
   - `pulseboard-api`
   - `pulseboard-celery-worker`
4. Fill every `sync: false` environment variable:

```text
DATABASE_URL=<Neon connection string>
REDIS_URL=<Redis TLS URL>
CELERY_BROKER_URL=<Redis TLS URL>
CELERY_RESULT_BACKEND=<Redis TLS URL>
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
PUBLIC_SHARE_BASE_URL=https://your-vercel-app.vercel.app
```

After the first successful API deploy, check:

```text
https://your-render-api.onrender.com/api/v1/health
```

It should return:

```json
{"status":"ok"}
```

## 4. Deploy Frontend On Vercel

1. Import the same GitHub repo into Vercel.
2. Set the Vercel project root directory to `apps/web`.
3. Add production environment variables:

```text
API_INTERNAL_URL=https://your-render-api.onrender.com/api/v1
NEXT_PUBLIC_API_URL=/api/backend
```

Deploy the Vercel project.

After Vercel gives you the production URL, return to Render and update both services:

```text
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
PUBLIC_SHARE_BASE_URL=https://your-vercel-app.vercel.app
```

Redeploy the Render API and worker.

## 5. Seed Public Demo Data

After migrations run successfully, open a Render shell for `pulseboard-api` and run:

```bash
python -m scripts.demo_data
```

Seed login:

```text
owner@example.com
Password123!
```

Public demo dashboard:

```text
https://your-vercel-app.vercel.app/share/demo-growth-overview
```

## 6. Smoke Test Production

From a shell that can reach the public API:

```bash
SMOKE_BASE_URL=https://your-render-api.onrender.com/api/v1 python -m scripts.live_smoke
```

Then verify in the browser:

- Sign in
- Create an API key
- Send an event
- Create a dashboard/widget
- Share the dashboard

## Notes

- Do not use the local Docker Postgres database for public deployment.
- Keep `COOKIE_SECURE=true` in production.
- Keep `NEXT_PUBLIC_API_URL=/api/backend`; the frontend proxy calls the Render API server-side.
- Render can run the API and worker from the production Dockerfile in `apps/api/Dockerfile.prod`.
- The local Docker setup remains unchanged.

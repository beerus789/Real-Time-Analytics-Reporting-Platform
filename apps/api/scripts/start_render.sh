#!/bin/sh
set -eu

alembic upgrade head

celery -A app.core.celery_app.celery_app worker \
  --loglevel=INFO \
  -Q ingestion \
  --concurrency="${CELERY_CONCURRENCY:-1}" &
CELERY_PID="$!"

cleanup() {
  kill "$CELERY_PID" 2>/dev/null || true
}
trap cleanup INT TERM

uvicorn app.main:create_app \
  --factory \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"

cleanup

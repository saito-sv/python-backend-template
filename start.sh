#!/bin/bash

uv run python -m app.database.wait

if [ "$RUN_MIGRATIONS_ON_STARTUP" = "true" ]; then
  echo "Running migrations on startup"
  uv run python -m alembic upgrade head
else
  echo "Not running migrations on startup"
fi

if [ "$ENVIRONMENT" != "production" ]; then
  echo "Starting application with hot reloading enabled"
  uv run python -m uvicorn app.app:app --port 8000 --host 0.0.0.0 --reload --proxy-headers --forwarded-allow-ips='*'
else
  echo "Starting application with production environment"
  uv run python -m uvicorn app.app:app --port 8000 --host 0.0.0.0 --proxy-headers --forwarded-allow-ips='*'
fi

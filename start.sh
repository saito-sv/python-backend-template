#!/bin/bash
set -euo pipefail

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"

uv run --frozen --no-dev python -m app.database.wait

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  echo "Running migrations on startup"
  export GOOSE_DBSTRING="$(uv run --frozen --no-dev python migrations/env.py)"
  goose -dir migrations postgres up
else
  echo "Not running migrations on startup"
fi

if [ "${APP_ENVIRONMENT:-development}" != "production" ]; then
  echo "Starting application with hot reloading enabled on ${APP_HOST}:${APP_PORT}"
  exec uv run --frozen python -m uvicorn app.app:app --host "$APP_HOST" --port "$APP_PORT" --reload --proxy-headers --forwarded-allow-ips='*'
else
  echo "Starting application in production mode on ${APP_HOST}:${APP_PORT}"
  exec uv run --frozen --no-dev python -m uvicorn app.app:app --host "$APP_HOST" --port "$APP_PORT" --proxy-headers --forwarded-allow-ips='*'
fi

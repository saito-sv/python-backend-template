set fallback := true
set dotenv-load := true

run := "uv run --"

# Default: format, lint, test
default:
    #!/usr/bin/env bash
    exit_code=0
    just format || ((exit_code++))
    just lint || ((exit_code++))
    just test || ((exit_code++))
    exit $exit_code

# Install dependencies
install:
    uv sync

# Format code
format *FILES='.':
    {{run}} ruff check --fix {{FILES}}
    {{run}} ruff format {{FILES}}

# Lint code
lint *FILES='.':
    {{run}} ruff check {{FILES}}
    {{run}} ruff format --check {{FILES}}
    {{run}} pyright {{FILES}}

# Run all tests (integration tests need `just db && just migrate-up`)
test *ARGS:
    {{run}} pytest {{ARGS}}

# Run unit tests only
test-unit:
    {{run}} pytest tests/unit

# Run integration tests only
test-integration:
    {{run}} pytest tests/integration

# Run tests with coverage
test-cov:
    {{run}} pytest --cov=app --cov-report=html --cov-report=term

# Start dev server (starts DB first)
dev:
    just db
    ./start.sh

# Start database services
db:
    docker compose up -d --wait database redis rabbitmq

# Start the local Grafana stack (Tempo, Prometheus, Loki) at http://localhost:3000; set OTEL_ENABLED=true
otel:
    docker compose --profile otel up -d otel-lgtm

# Stop database services
db-down:
    docker compose down

# Destroy database (removes volumes)
destroy-db:
    docker compose down -v

# Reset database
reset-db:
    just destroy-db
    just db
    just migrate-up

# Apply migrations
migrate-up:
    #!/usr/bin/env bash
    set -euo pipefail
    export GOOSE_DBSTRING="$(uv run --quiet -- python migrations/env.py)"
    goose -dir migrations postgres up

# Rollback last migration
migrate-down:
    #!/usr/bin/env bash
    set -euo pipefail
    export GOOSE_DBSTRING="$(uv run --quiet -- python migrations/env.py)"
    goose -dir migrations postgres down

# Show migration status
migrate-status:
    #!/usr/bin/env bash
    set -euo pipefail
    export GOOSE_DBSTRING="$(uv run --quiet -- python migrations/env.py)"
    goose -dir migrations postgres status

# Create a new migration file
migrate-gen NAME:
    goose -dir migrations create {{NAME}} sql

# Start task worker
task-worker:
    bash task_queue/start-worker.sh

# Clean up cache
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf htmlcov .coverage

# Show help
help:
    @just --list

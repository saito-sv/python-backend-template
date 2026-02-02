set fallback := true

run := "uv run --"

# Default: run format, lint, and test
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
    {{run}} ruff check --fix {{FILES}}
    {{run}} ruff format --check {{FILES}}
    {{run}} pyright {{FILES}}

# Apply unsafe fixes (use with caution)
unsafe-fix:
    {{run}} ruff check --fix --unsafe-fixes .
    {{run}} ruff format .

# Run all tests
test:
    {{run}} pytest

# Run unit tests only
test-unit:
    {{run}} pytest tests/unit -v

# Run integration tests only
test-integration:
    {{run}} pytest tests/integration -v

# Run tests with coverage
test-cov:
    {{run}} pytest --cov=app --cov-report=html --cov-report=term

# Start development server
dev *OPTIONS:
    ./start.sh {{OPTIONS}}

# Start database services
db:
    docker-compose up -d database redis rabbitmq

# Stop database services
db-down:
    docker-compose down

# Create a new migration (autogenerate from models)
migrate-gen MESSAGE:
    {{run}} alembic revision --autogenerate -m "{{MESSAGE}}"
    just format alembic/versions

# Apply migrations
migrate-up:
    {{run}} alembic upgrade head

# Rollback migrations
migrate-down STEPS="-1":
    {{run}} alembic downgrade {{STEPS}}

# Redo a migration (rollback, delete, regenerate, apply)
migrate-redo MESSAGE:
    #!/usr/bin/env bash
    set -eou pipefail
    snake_case_message=$(echo "{{MESSAGE}}" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    file=alembic/versions/*${snake_case_message}.py
    if [ -f $file ]; then
        down_revision=$(grep 'down_revision' $file | sed -r 's/.*down_revision.*=.*"(.*)".*/\1/')
        if [[ "$down_revision" != "None" ]]; then
            just migrate-down $down_revision
        else
            just migrate-down base
        fi
        rm $file
    fi
    just migrate-gen "{{MESSAGE}}"
    just migrate-up

# Reset database (down and up)
reset-db:
    just db-down
    just db
    sleep 3
    just migrate-up

# Start task worker
task-worker:
    {{run}} taskiq worker app.tasks:broker

# Clean up cache and build artifacts
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf htmlcov .coverage

# Show help
help:
    @just --list

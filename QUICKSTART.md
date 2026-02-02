# Quick Start Guide

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv)

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env and set your SECRET_KEY
```

### 3. Start Services

```bash
# Start database, Redis, and RabbitMQ
just db

# Wait for services to be ready
sleep 5
```

### 4. Run Migrations

```bash
just migrate-up
```

### 5. Start the API

```bash
just dev
```

The API is now running at `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Try It Out

### Create a User

```bash
curl -X POST http://localhost:8000/user/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "secretpassword",
    "full_name": "Test User"
  }'
```

### Get All Users

```bash
curl http://localhost:8000/user/
```

## Next Steps

1. **Add Your Domain**: Copy the `app/domains/user/` structure for your own domains
2. **Add Routes**: Include your routers in `app/routes.py`
3. **Write Tests**: Add tests in `tests/unit/` and `tests/integration/`

## Common Commands

```bash
# Format code
just format

# Run linting
just lint

# Run tests
just test

# Create migration
just migrate-gen "your migration message"

# Apply migrations
just migrate-up

# Reset database
just reset-db
```

## Project Structure

```
app/
├── domains/          # Business domains
│   └── user/         # Example user domain
├── database/         # Database configuration
├── di/               # Dependency injection utilities
├── repository/       # Base repository classes
├── exc.py            # Common exceptions
└── app.py            # FastAPI application

settings/             # Configuration
tests/                # Tests
alembic/              # Database migrations
task_queue/           # Background tasks
```

## Dependency Injection

```python
from dataclasses import dataclass
from antidote import injectable
from app.domains.user.repository import UserRepository

@injectable
@dataclass
class MyService:
    user_repository: UserRepository
    
    async def do_something(self):
        users = await self.user_repository.get_all()
        return users
```

## Additional Documentation

- Check the main [README.md](README.md) for detailed documentation
- Review the example `user` domain for patterns
- The template uses standard FastAPI patterns

# FastAPI Backend Template

Production-ready FastAPI backend template with modern Python patterns, type safety, and best practices.

## Features

- **FastAPI** - Modern web framework for building APIs with automatic OpenAPI docs
- **SQLModel** - Type-safe ORM with Pydantic integration for database models
- **PostgreSQL** - Relational database
- **Alembic** - Database migration management
- **Repository Pattern** - Clean data access layer with composable filters
- **Object ID Generation** - Prefixed IDs (e.g., `usr_abc123...`)
- **Antidote** - Dependency injection for testable, maintainable code
- **TaskIQ** - Background task queue with RabbitMQ/Redis support
- **Modern Tooling** - uv for package management, ruff for linting/formatting, pyright for type checking
- **Docker** - Complete development environment with docker-compose

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

```bash
# Install dependencies
uv sync

# Start services (PostgreSQL, Redis, RabbitMQ)
docker-compose up -d

# Run migrations
uv run alembic upgrade head

# Start development server
just dev
```

Visit http://localhost:8000/docs for interactive API documentation.

## Project Structure

```
backend-template/
├── app/
│   ├── app.py                    # FastAPI application setup
│   ├── exc.py                    # Common exception classes
│   ├── database/
│   │   ├── engine.py             # Database connection
│   │   ├── session.py            # Session management
│   │   └── model_base.py         # Base models with ID generation
│   ├── repository/
│   │   ├── base.py               # Base repository with CRUD operations
│   │   ├── filter.py             # Filter pattern for composable queries
│   │   └── exceptions.py         # Repository exceptions
│   ├── di/
│   │   └── hidden_inject.py      # DI utilities
│   └── domains/                  # Business domains (singular names)
│       └── user/                 # Example user domain
│           ├── models.py         # Database models
│           ├── schemas.py        # API request/response schemas
│           ├── repository.py     # Data access layer
│           ├── service.py        # Business logic
│           ├── router.py         # API endpoints
│           └── tasks.py          # Background tasks
├── settings/
│   └── config.py                 # Application configuration
├── alembic/                      # Database migrations
├── task_queue/                   # Background job definitions
├── tests/                        # Test suite
├── pyproject.toml                # Project dependencies and config
├── justfile                      # Task automation commands
└── docker-compose.yml            # Local development services
```

## Architecture Patterns

### Object ID Generation

Models use prefixed IDs for better debugging and type safety:

```python
from app.database.model_base import BaseIDTableModelFactory

ID_PREFIX = "usr"

class User(BaseIDTableModelFactory(ID_PREFIX), table=True):
    __tablename__ = "user"
    
    email: str = Field(unique=True, index=True)
    full_name: str | None = None
```

Generated IDs: `usr_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Repository Pattern with Filters

Composable filters for database queries:

```python
@dataclass
class _EmailFilter(DataFilter[User]):
    email: str
    
    @property
    def expression(self) -> Any:
        return User.email == self.email

# Usage
user = await repo.get_one(repo.email_filter("john@example.com"))
```

Combine filters for complex queries:

```python
users = await repo.get_all(
    repo.is_active_filter(True),
    repo.email_search_filter("john"),
)
```

### Domain-Driven Design

Each domain follows a layered architecture:

```
domains/user/
├── models.py       # Database entities (SQLModel)
├── schemas.py      # API contracts (Pydantic)
├── repository.py   # Data access with filters
├── service.py      # Business logic
├── router.py       # HTTP endpoints
└── tasks.py        # Background tasks
```

### Dependency Injection

Services use Antidote for dependency injection:

```python
from dataclasses import dataclass
from antidote import injectable
from app.domains.user.repository import UserRepository

@injectable
@dataclass
class UserService:
    repository: UserRepository
    
    async def create_user(self, user_data: UserCreate) -> UserRead:
        return await self.repository.create(user_data)
```

### Background Tasks

TaskIQ for async background job processing:

```python
from task_queue import task
from app.database.engine import async_session_factory
from app.domains.user.repository import UserRepository

@task
async def send_welcome_email(user_id: str) -> None:
    async with async_session_factory() as session:
        repository = UserRepository(session_factory=async_session_factory)
        user = await repository.get_by_id(user_id)
        # Send email logic
```

Enqueue tasks:

```python
await send_welcome_email.kiq(user_id="usr_123...")
```

## Development

### Available Commands

```bash
just install          # Install dependencies
just dev              # Start development server
just test             # Run all tests
just lint             # Run ruff linter
just format           # Format code with ruff
just db               # Start database services
just migrate-gen "msg" # Create new migration
just migrate-up       # Apply migrations
just migrate-down     # Rollback last migration
```

### Database Migrations

Development workflow:

```bash
# Create migration after modifying models
just migrate-gen "add user table"

# Apply migrations
just migrate-up

# Rollback if needed
just migrate-down
```

Production workflow:

Set `RUN_MIGRATIONS_ON_STARTUP=true` to automatically run migrations on application startup.

### Code Quality

```bash
# Format code
just format

# Check linting
just lint

# Type checking
uv run pyright .
```

## Creating a New Domain

1. Create domain directory:
   ```bash
   mkdir -p app/domains/product
   ```

2. Define the model (`models.py`):
   ```python
   from sqlmodel import Field, SQLModel
   from app.database.model_base import BaseIDTableModelFactory, BaseRead
   
   ID_PREFIX = "prd"
   
   class ProductBase(SQLModel):
       name: str
       price: int
       description: str | None = None
   
   class Product(ProductBase, BaseIDTableModelFactory(ID_PREFIX), table=True):
       __tablename__ = "products"
       name: str = Field(index=True, nullable=False)
       price: int = Field(nullable=False)
   
   class ProductCreate(ProductBase):
       pass
   
   class ProductUpdate(SQLModel):
       name: str | None = None
       price: int | None = None
       description: str | None = None
   
   class ProductRead(ProductBase, BaseRead):
       pass
   ```

3. Create repository (`repository.py`):
   ```python
   from dataclasses import dataclass
   from typing import Any
   from antidote import injectable
   from app.repository.base import MainObjectIdRepository
   from app.repository.filter import DataFilter
   from .models import Product, ProductCreate, ProductRead, ProductUpdate
   
   @dataclass
   class _NameFilter(DataFilter[Product]):
       name: str
       
       @property
       def expression(self) -> Any:
           return Product.name == self.name
   
   @injectable(lifetime="transient")
   class ProductRepository(MainObjectIdRepository[ProductCreate, ProductRead, ProductUpdate, Product]):
       _db_class = Product
       _read_class = ProductRead
       
       @classmethod
       def name_filter(cls, name: str) -> _NameFilter:
           return _NameFilter(name=name)
   ```

4. Create service (`service.py`):
   ```python
   from dataclasses import dataclass
   from antidote import injectable
   from .repository import ProductRepository
   from .models import ProductCreate, ProductRead
   
   @injectable
   @dataclass
   class ProductService:
       repository: ProductRepository
       
       async def create_product(self, data: ProductCreate) -> ProductRead:
           return await self.repository.create(data)
   ```

5. Create router (`router.py`):
   ```python
   from fastapi import APIRouter
   from antidote import inject
   from app.di import hidden_inject
   from .service import ProductService
   from .models import ProductCreate, ProductRead
   
   router = APIRouter(prefix="/products", tags=["products"])
   
   @router.post("/", response_model=ProductRead)
   @hidden_inject
   async def create_product(
       data: ProductCreate,
       service: ProductService = inject.me(),
   ) -> ProductRead:
       return await service.create_product(data)
   ```

6. Register router in `app/routes.py`:
   ```python
   from app.domains.product.router import router as product_router
   
   def register_routes(app: FastAPI) -> None:
       app.include_router(product_router)
   ```

7. Create migration:
   ```bash
   just migrate-gen "add product table"
   just migrate-up
   ```

## Testing

```bash
# Run all tests
just test

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_user.py
```

## Docker

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop services
docker-compose down
```

Services included:
- **database** - PostgreSQL 16
- **redis** - Redis 7
- **rabbitmq** - RabbitMQ 3 with management UI
- **api** - FastAPI application server
- **worker** - TaskIQ worker process

### Production Deployment

Run two separate services:

1. **API Server** - Handles HTTP requests
2. **Worker Process** - Processes background tasks

Environment configuration:

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/dbname

# Redis
REDIS_HOST=redis-host
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=rabbitmq-host
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=admin
RABBITMQ_PASSWORD=password

# Task Queue
TASK_QUEUE_USE_IN_MEMORY_BROKER=false
```

Docker deployment:

```bash
# Build image
docker build -t my-api:latest .

# Run API server
docker run -d \
  --name api \
  -p 8000:8000 \
  --env-file .env.production \
  my-api:latest \
  uvicorn app.app:app --host 0.0.0.0 --port 8000

# Run worker process
docker run -d \
  --name worker \
  --env-file .env.production \
  my-api:latest \
  bash task_queue/start-worker.sh
```

## Configuration

Configuration via environment variables and `settings/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Secret key for JWT tokens

## Key Technologies

- **[FastAPI](https://fastapi.tiangolo.com/)** - Web framework
- **[SQLModel](https://sqlmodel.tiangelo.com/)** - SQL databases with Python type annotations
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migration tool
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[Antidote](https://antidote.readthedocs.io/)** - Dependency injection framework
- **[TaskIQ](https://taskiq-python.github.io/)** - Distributed task queue
- **[uv](https://github.com/astral-sh/uv)** - Python package installer
- **[ruff](https://github.com/astral-sh/ruff)** - Python linter and formatter
- **[pyright](https://github.com/microsoft/pyright)** - Static type checker

## License

MIT License

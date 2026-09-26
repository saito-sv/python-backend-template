# FastAPI Backend Template

FastAPI backend template with a repository pattern, SQL-first migrations and prefixed ULID ids.

## Stack

- **FastAPI** + **SQLModel** (async SQLAlchemy) + **PostgreSQL**
- **goose** for migrations (plain SQL files in `migrations/`)
- **Antidote** for dependency injection
- **TaskIQ** for background tasks (RabbitMQ + Redis, or in-memory for dev)
- **OpenTelemetry** to the Grafana stack: Tempo (traces), Mimir/Prometheus (metrics), Loki (logs)
- **`.env`** for configuration (pydantic-settings)
- **uv**, **ruff**, **pyright**, **just**

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [goose](https://github.com/pressly/goose): `brew install goose` or `go install github.com/pressly/goose/v3/cmd/goose@latest`
- [Docker](https://www.docker.com/) and [just](https://github.com/casey/just)

## Getting Started

```bash
uv sync
cp .env.example .env
just db           # Postgres, Redis, RabbitMQ
just migrate-up   # apply goose migrations
just dev          # http://localhost:8000/docs
```

See [QUICKSTART.md](QUICKSTART.md) for example requests.

## Project Structure

```
.
├── app/
│   ├── app.py              # create_app(): middleware, exception handlers, routers
│   ├── routes.py           # RouteConfig + auto-discovery of domain routers
│   ├── exc.py              # Exception hierarchy
│   ├── telemetry.py        # OpenTelemetry setup (traces, metrics, logs)
│   ├── config/loader.py    # Env-based config modules (APP_, DATABASE_, REDIS_, ...)
│   ├── database/           # Engine, session manager, model base (ULID ids), DB wait script
│   ├── repository/         # Base repositories, filters, ILIKE search
│   ├── di/                 # hidden_inject for FastAPI routes
│   ├── utils/              # Shared API types (BaseRead, cursor pagination, NormalizedEmail), exception handlers
│   └── domains/<domain>/
│       ├── constants.py    # ID prefix and enums (typed Final)
│       ├── models.py       # Everything touching the DB: table model + repository write shapes
│       ├── schemas.py      # API types only: request/response models
│       ├── repository.py   # Data access + filters
│       ├── service.py      # Business logic
│       ├── router.py       # Endpoints + `route_config` (auto-registered)
│       └── tasks.py        # Optional background tasks
├── migrations/             # goose SQL migrations + env.py (prints GOOSE_DBSTRING)
├── task_queue/             # TaskIQ broker, @task decorator, worker entry point
├── justfile, start.sh, Dockerfile, docker-compose.yml
```

## Key Conventions

### The database owns the schema

Tables are created by **goose SQL migrations**, not generated from models. That means:

- Table classes in `models.py` only declare columns and types. Don't put `unique=True`, `index=True`, `nullable=False`, `max_length` or `server_default` on them.
- Constraints, indexes, defaults, foreign keys and triggers all live in the SQL migration.
- Request validation such as max length or email format belongs in the API schemas (`schemas.py`).
- `models.py` is for anything that touches the DB (the table and the shapes the repository writes); `schemas.py` is for API types only and never imports the table.
- Module-level constants are typed `Final` (e.g. `USER_ID_PREFIX: Final = "usr"`).

```python
# app/domains/post/models.py
class PostBase(SQLModel):
    user_id: str = Field(foreign_key="users.id")  # only needed for ORM joins
    title: str
    content: str


class Post(PostBase, BaseIDTableModelFactory(POST_ID_PREFIX), table=True):
    __tablename__ = "posts"
```

### IDs, timestamps and soft delete

`BaseIDTableModelFactory(prefix)` adds these fields:

- `id` is a prefixed lowercase ULID, e.g. `usr_01j9z3k6v7f8g9h0j1k2m3n4p5` (stored as `varchar(255)`)
- `created_at` / `updated_at` are tz-aware (`timestamptz`)
- `deleted_at` is used for soft delete

Every table needs these columns in its migration, plus the `updated_at` trigger:

```sql
id          varchar(255) PRIMARY KEY,
created_at  timestamptz  NOT NULL DEFAULT now(),
updated_at  timestamptz  NOT NULL DEFAULT now(),
deleted_at  timestamptz
```

### Repositories

Repositories extend `MainObjectIdRepository[Create, Read, Update, DB]`:

- The session factory defaults to `app.database.engine.async_session_factory`; pass another to the constructor if needed.
- Reads exclude soft-deleted rows by default. Pass `include_deleted=True` to include them.
- `delete_by_id(id)` soft-deletes. Use `delete_by_id(id, hard=True)` for a hard delete.
- `update()` bumps `updated_at` automatically.
- `paginate(...)` does keyset pagination on the ULID `id` (see [Pagination](#pagination)).
- Filters are small dataclasses and can be combined with `and_filter`, `or_filter` and `not_filter`.

```python
@dataclass
class _EmailFilter(DataFilter[User]):
    email: str

    @property
    def expression(self) -> Any:
        return User.email == self.email


@injectable(lifetime="transient")
class UserRepository(MainObjectIdRepository[UserDBCreate, UserRead, UserDBUpdate, User]):
    _db_class = User
    _read_class = UserRead

    @staticmethod
    def email_filter(email: str) -> DataFilter[User]:
        return _EmailFilter(email)
```

### Services and routers

```python
@injectable
class PostService:
    @inject
    def __init__(self, post_repo: PostRepository = inject.me()) -> None:
        self._post_repo = post_repo
```

Each `router.py` exposes a module-level `route_config`. `app/routes.py` discovers them automatically and mounts them under `/v1`; there is no list to update.

```python
router = APIRouter()

@router.get("/posts/{post_id}")
@hidden_inject
async def get_post(post_id: str, post_service: PostService = inject.me()) -> PostRead:
    return await post_service.get_post(post_id)

route_config = RouteConfig(router=router, prefix="", tags=["posts"])
```

Raise exceptions from `app.exc` such as `EntityNotFoundException` (404) or `EntityExistsException` (409) and the default handlers return the right status. Unique and foreign key violations from Postgres come back as 409.

## Migrations

`migrations/env.py` builds `GOOSE_DBSTRING` from the `DATABASE_*` settings.

```bash
just migrate-gen add_comments_table   # creates migrations/<timestamp>_add_comments_table.sql
just migrate-up                       # apply pending migrations
just migrate-down                     # roll back the last migration
just migrate-status
```

`start.sh` runs `goose up` on startup unless `RUN_MIGRATIONS_ON_STARTUP=false`.

## Adding a Domain

1. `just migrate-gen create_<things>_table`, then write the SQL (base columns + `updated_at` trigger), then run `just migrate-up`.
2. Create `app/domains/<thing>/` with `constants.py`, `models.py`, `schemas.py`, `repository.py`, `service.py` and `router.py` (with `route_config`).
3. You're done. The router is picked up automatically.

## Configuration

All settings come from environment variables, with `.env` as the fallback. See `.env.example`.

| Prefix | Module | Notes |
|---|---|---|
| `APP_` | `AppConfig` | name, host, port, environment, debug, CORS |
| `DATABASE_` | `DatabaseConfig` | host, port, name, username, password, echo |
| `REDIS_` | `RedisConfig` | task result backend |
| `RABBITMQ_` | `RabbitMQConfig` | task broker |
| `TASK_QUEUE_` | `TaskQueueConfig` | `USE_IN_MEMORY_BROKER=true` for local dev |
| `OTEL_` | `TelemetryConfig` | `ENABLED`, `SERVICE_NAME`, `SERVICE_NAMESPACE`, `LOG_LEVEL`, `CONSOLE_EXPORTER` |

In code, load only the modules you need: `load("database")`.

## Pagination

List endpoints use cursor (keyset) pagination on the id. Ids are ULIDs, so they sort by
creation time, and each page is a primary-key range scan however deep you go. Offsets and
total counts are deliberately not offered.

```
GET /v1/users?limit=50&order=desc
→ {"items": [...], "next_cursor": "usr_01j9z3k6v7f8g9h0j1k2m3n4p5"}

GET /v1/users?limit=50&order=desc&cursor=usr_01j9z3k6v7f8g9h0j1k2m3n4p5
→ {"items": [...], "next_cursor": null}   # last page
```

In a domain, accept `params: CursorParams = Depends()`, return `CursorPage[ReadModel]`, and
call `repo.paginate(*filters, cursor=params.cursor, limit=params.limit, order=params.order)`.

## Observability

OpenTelemetry is set up in `app/telemetry.py` and is off by default (`OTEL_ENABLED=false`).
It targets the Grafana stack: the API and the worker send all three signals over OTLP/HTTP to
one endpoint, which routes them to the right backend.

| Signal | Backend | Query language | What you get |
|---|---|---|---|
| Traces | Tempo | TraceQL | a span per request, a child span per SQL statement, task spans in the enqueuing request's trace |
| Metrics | Mimir / Prometheus | PromQL | `http_server_request_duration_seconds` (by `http_route`, `http_request_method`, `http_response_status_code`), active requests, DB pool usage |
| Logs | Loki | LogQL | every `logging` record, with `trace_id`/`span_id` so Grafana links a log line to its trace |

Every signal carries `service.name`, `service.namespace`, `service.version` and
`deployment.environment` (from `APP_ENVIRONMENT`). Grafana builds the Prometheus `job` label as
`<namespace>/<name>`. HTTP metrics use the stable OTel semantic conventions, the names Grafana
dashboards and Application Observability expect.

### Grafana Cloud

In your stack go to **Details → OpenTelemetry**, create a token with metrics, logs and traces
write scopes, then set:

```bash
OTEL_ENABLED=true
OTEL_SERVICE_NAME=my-api
OTEL_SERVICE_NAMESPACE=my-team
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp-gateway-prod-<region>.grafana.net/otlp
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic%20<base64 of instanceId:token>
```

If you run Grafana Alloy (or any OTel collector) as a sidecar or agent, point
`OTEL_EXPORTER_OTLP_ENDPOINT` at it instead and keep the credentials in the collector.

### Locally

```bash
just otel                  # grafana/otel-lgtm: Grafana at http://localhost:3000
OTEL_ENABLED=true just dev
```

`grafana/otel-lgtm` runs the same pipeline (OTel collector → Tempo, Prometheus, Loki) with the
data sources and trace↔log links already wired. For a quick look with no collector, use
`OTEL_ENABLED=true OTEL_CONSOLE_EXPORTER=true just dev`.

Stdout logs always include `trace_id`/`span_id`, even with OTel off. Other standard variables
work as usual: `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_TRACES_SAMPLER` / `OTEL_TRACES_SAMPLER_ARG`,
and `OTEL_{TRACES,METRICS,LOGS}_EXPORTER=none` to turn a signal off.

Custom spans:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("charge_card") as span:
    span.set_attribute("user.id", user_id)
    ...
```

## Background Tasks

```python
@task
@inject
async def send_welcome_email(user_id: str, user_service: UserService = inject.me()) -> None:
    ...

await send_welcome_email.kiq(user_id="usr_...")
```

Start a worker with `just task-worker`.

## Docker

```bash
docker compose up -d                         # infra only
docker compose --profile app up -d --build   # + api and worker
```

The image includes goose, so the API container applies migrations on startup.


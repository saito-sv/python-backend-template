# Quick Start

## Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- [goose](https://github.com/pressly/goose)
- Docker and [just](https://github.com/casey/just)

## Setup

```bash
uv sync
cp .env.example .env
just db
just migrate-up
just dev
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Try It Out

```bash
# Create a user
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secret", "full_name": "Test User"}'

# List users (cursor pagination: pass the returned next_cursor to get the next page)
curl "http://localhost:8000/v1/users?limit=20"
curl "http://localhost:8000/v1/users?limit=20&cursor=usr_..."

# Create a post (use the id returned above)
curl -X POST http://localhost:8000/v1/posts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "usr_...", "title": "Hello", "content": "World"}'

# Posts for a user
curl http://localhost:8000/v1/users/usr_.../posts
```

## Next Steps

1. Write a migration: `just migrate-gen create_things_table`, then run `just migrate-up`.
2. Copy `app/domains/post/` as a starting point for your domain.
3. See [README.md](README.md) for the conventions.

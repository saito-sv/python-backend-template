# Sandbox Image Guide: Build, Deploy & Expose

This guide walks you through creating your own sandbox Docker image from this FastAPI backend template, deploying it, and exposing it so it can be accessed from the outside world.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Understand the Existing Dockerfile](#step-1--understand-the-existing-dockerfile)
4. [Step 2 — Customise & Build Your Image](#step-2--customise--build-your-image)
5. [Step 3 — Run & Verify Locally](#step-3--run--verify-locally)
6. [Step 4 — Deploy with Docker Compose (Full Stack)](#step-4--deploy-with-docker-compose-full-stack)
7. [Step 5 — Expose the Service](#step-5--expose-the-service)
8. [Step 6 — Production Hardening Tips](#step-6--production-hardening-tips)
9. [Common Commands Reference](#common-commands-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The workspace contains a production-ready **FastAPI** backend. The flow for turning it into a running, reachable sandbox is:

```
Your code
   ↓  docker build
Docker image
   ↓  docker run / docker-compose up
Running container(s)
   ↓  port mapping / reverse proxy
Exposed endpoint (localhost or public URL)
```

---

## Prerequisites

Install the following tools before you start:

| Tool | Minimum version | Install |
|---|---|---|
| Docker | 24+ | https://docs.docker.com/get-docker/ |
| Docker Compose | 2.x (plugin) | bundled with Docker Desktop |
| `uv` (Python pkg manager) | latest | `curl -Ls https://astral.sh/uv/install.sh \| sh` |
| `just` (task runner) | latest | `cargo install just` or `brew install just` |

Verify everything is working:

```bash
docker --version
docker compose version
uv --version
just --version
```

---

## Step 1 — Understand the Existing Dockerfile

The `Dockerfile` at the root of the project already covers the essentials:

```dockerfile
FROM python:3.12-slim                              # (1) slim base image

WORKDIR /app

# (2) system-level C compiler + psql client needed by asyncpg
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# (3) copy uv binary from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# (4) install only production deps (no dev/test packages)
COPY pyproject.toml ./
RUN uv sync --frozen --no-dev

# (5) copy the rest of the source code
COPY . .

RUN chmod +x start.sh

EXPOSE 8000                                        # (6) document the listening port

CMD ["./start.sh"]                                 # (7) default startup command
```

### What `start.sh` does

```bash
# Waits for the database to be reachable
uv run python -m app.database.wait

# Optionally runs Alembic migrations (controlled by RUN_MIGRATIONS_ON_STARTUP)
if [ "$RUN_MIGRATIONS_ON_STARTUP" = "true" ]; then
  uv run alembic upgrade head
fi

# Starts uvicorn (with hot-reload outside production)
if [ "$ENVIRONMENT" != "production" ]; then
  uv run uvicorn app.app:app --port 8000 --host 0.0.0.0 --reload ...
else
  uv run uvicorn app.app:app --port 8000 --host 0.0.0.0 ...
fi
```

> **Key insight:** The image is the same for every environment. Behaviour is controlled entirely via environment variables — no need to rebuild for dev vs. production.

---

## Step 2 — Customise & Build Your Image

### 2a. Set up your environment file

```bash
cp .env.template .env
```

Open `.env` and update at minimum:

```dotenv
SECRET_KEY=replace-with-a-long-random-string   # required for JWT signing
ENVIRONMENT=development                          # or production
```

Generate a secure secret key if you need one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2b. (Optional) Customise the image

**Add extra system packages** (e.g., `curl` for healthchecks):

```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \                    # ← add here
    && rm -rf /var/lib/apt/lists/*
```

**Add a Python dependency** — edit `pyproject.toml`:

```toml
dependencies = [
    ...
    "httpx>=0.27.0",   # ← example new dependency
]
```

Then regenerate the lockfile so the frozen install stays reproducible:

```bash
uv lock
```

**Change the default port** — update both `EXPOSE` and the uvicorn command in `start.sh` if you want to use a port other than `8000`.

### 2c. Build the image

```bash
# Basic build — image tagged as my-sandbox:latest
docker build -t my-sandbox:latest .

# Build for a specific platform (useful for M1/M2 Macs targeting Linux servers)
docker build --platform linux/amd64 -t my-sandbox:latest .

# Build with a version tag
docker build -t my-sandbox:1.0.0 -t my-sandbox:latest .
```

Confirm the image was created:

```bash
docker images my-sandbox
```

---

## Step 3 — Run & Verify Locally

Run a **single container** (useful for quick smoke tests — no database needed):

```bash
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  -e TASK_QUEUE_USE_IN_MEMORY_BROKER=true \
  my-sandbox:latest
```

> `TASK_QUEUE_USE_IN_MEMORY_BROKER=true` skips RabbitMQ/Redis so the container starts without any external services.

Open your browser or run:

```bash
curl http://localhost:8000/health
# → {"status":"healthy"}

# Interactive Swagger UI (open in browser)
open http://localhost:8000/docs
```



---

## Step 4 — Deploy with Docker Compose (Full Stack)

The `docker-compose.yml` spins up the **complete sandbox environment** — API, database, Redis, RabbitMQ, and background worker — in one command.

### Service map

| Service | Image | Port(s) | Role |
|---|---|---|---|
| `database` | `postgres:16-alpine` | 5432 | Primary datastore |
| `redis` | `redis:7-alpine` | 6379 | Result backend / cache |
| `rabbitmq` | `rabbitmq:3-management-alpine` | 5672, 15672 | Task broker |
| `api` | Built from `Dockerfile` | **8000** | FastAPI HTTP server |
| `worker` | Built from `Dockerfile` | — | TaskIQ background worker |

### Start the full stack

```bash
# Build images and start all services in the background
docker compose up --build -d

# Follow logs from just the API service
docker compose logs -f api

# Follow logs from all services at once
docker compose logs -f
```

### Run database migrations

```bash
# Option A — run from your host (uv must be installed locally)
uv run alembic upgrade head

# Option B — run inside the running api container
docker compose exec api uv run alembic upgrade head

# Option C — let start.sh handle it automatically on every startup
# In .env:  RUN_MIGRATIONS_ON_STARTUP=true
```

### Verify all services are healthy

```bash
docker compose ps
```

You should see `(healthy)` next to `database`, `redis`, and `rabbitmq` before `api` and `worker` start accepting traffic.

```bash
curl http://localhost:8000/health
# → {"status":"healthy"}
```

### Stop the stack

```bash
docker compose down        # stops containers, keeps volumes (data preserved)
docker compose down -v     # stops containers AND deletes volumes (resets DB)
```

---

## Step 5 — Expose the Service

### Option A — Localhost only (default)

Docker binds port 8000 on `0.0.0.0` by default, so on your local machine it is immediately reachable at `http://localhost:8000`.

### Option B — Expose on your LAN

No extra steps needed. Other machines on the same network can reach your sandbox at:

```
http://<your-machine-ip>:8000
```

Find your local IP:

```bash
# macOS / Linux
hostname -I | awk '{print $1}'
```

### Option C — Expose publicly with a tunnel

Great for demos and sharing with remote collaborators without needing a server.

**ngrok:**

```bash
# Install: https://ngrok.com/download
ngrok http 8000
# → Forwarding  https://abc123.ngrok-free.app → http://localhost:8000
```

**Cloudflare Tunnel:**

```bash
# Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
cloudflared tunnel --url http://localhost:8000
```

Both tools print a public HTTPS URL you can share immediately — no DNS or firewall changes needed.

### Option D — Deploy to a cloud VM (EC2, Linode, DigitalOcean, etc.)

**1. Push your image to a registry:**

```bash
# Docker Hub
docker tag my-sandbox:latest yourusername/my-sandbox:latest
docker push yourusername/my-sandbox:latest

# GitHub Container Registry
docker tag my-sandbox:latest ghcr.io/yourusername/my-sandbox:latest
docker push ghcr.io/yourusername/my-sandbox:latest
```

**2. SSH into your VM and pull:**

```bash
ssh user@your-vm-ip
docker pull yourusername/my-sandbox:latest
```

**3. Copy your compose and env files to the VM, then start:**

```bash
scp docker-compose.yml .env user@your-vm-ip:~/app/
ssh user@your-vm-ip "cd ~/app && docker compose up -d"
```

**4. Open the firewall port:**

```bash
# Ubuntu UFW
sudo ufw allow 8000/tcp

# AWS — update your Security Group inbound rules via the console
# DigitalOcean / Linode — add a firewall rule via the control panel
```

**5. Access your sandbox:**

```
http://your-vm-ip:8000/health
http://your-vm-ip:8000/docs
```

### Option E — Add an Nginx reverse proxy (recommended for production)

Create `nginx.conf` alongside your `docker-compose.yml`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass         http://api:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Add an `nginx` service to `docker-compose.yml`:

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
```

Your API is now reachable on standard port **80**. Pair with [Certbot](https://certbot.eff.org/) for free HTTPS via Let's Encrypt.

---

## Step 6 — Production Hardening Tips

| Area | Recommendation |
|---|---|
| **Secrets** | Never commit `.env` to git. Use Docker Secrets, AWS Secrets Manager, or Vault. |
| **Migrations** | Set `RUN_MIGRATIONS_ON_STARTUP=true` or run them as a one-off init container. |
| **Environment** | Set `ENVIRONMENT=production` and `DEBUG=false` to disable hot-reload and verbose errors. |
| **Workers** | Scale the worker service independently: `docker compose up --scale worker=3 -d`. |
| **Health checks** | The `/health` endpoint is already wired — plug it into your load-balancer target group. |
| **Logging** | Add `--log-opt max-size=10m --log-opt max-file=3` to keep container logs bounded. |
| **CORS** | Restrict `CORS_ORIGINS` to your actual frontend domains in production. |
| **Database** | Use a managed PostgreSQL service (RDS, Cloud SQL, Supabase) instead of a Compose container in production. |
| **Reverse proxy** | Always put Nginx or a cloud load balancer in front; never expose uvicorn directly to the internet. |

---

## Common Commands Reference

```bash
# ── Image management ──────────────────────────────────────────
docker build -t my-sandbox:latest .           # build image
docker build --platform linux/amd64 -t my-sandbox:latest .  # cross-platform build
docker images my-sandbox                      # list images
docker rmi my-sandbox:latest                  # delete image

# ── Single container ──────────────────────────────────────────
docker run --rm -p 8000:8000 --env-file .env \
  -e TASK_QUEUE_USE_IN_MEMORY_BROKER=true \
  my-sandbox:latest                           # run ephemerally (no DB needed)

docker run -d --name sandbox \
  -p 8000:8000 --env-file .env \
  my-sandbox:latest                           # run as background daemon

docker logs -f sandbox                        # tail logs
docker exec -it sandbox bash                  # open a shell inside container
docker stop sandbox && docker rm sandbox      # stop and remove

# ── Docker Compose ────────────────────────────────────────────
docker compose up --build -d                  # build + start all services
docker compose ps                             # show service status
docker compose logs -f api                    # tail API logs
docker compose exec api bash                  # shell into api container
docker compose exec api uv run alembic upgrade head   # run migrations
docker compose down                           # stop (keep volumes)
docker compose down -v                        # stop + delete volumes (reset DB)
docker compose up --scale worker=3 -d        # scale worker to 3 instances

# ── Registry ──────────────────────────────────────────────────
docker login                                  # authenticate with Docker Hub
docker push yourusername/my-sandbox:latest    # push image
docker pull yourusername/my-sandbox:latest    # pull image

# ── just shortcuts (host-level dev) ──────────────────────────
just dev                     # start dev server locally (no Docker)
just db                      # start only the DB via Compose
just migrate-up              # apply Alembic migrations
just migrate-gen "message"   # auto-generate a new migration
just test                    # run the full test suite
just lint                    # run ruff + pyright checks
just format                  # auto-format code with ruff
```

---

## Troubleshooting

### Container exits immediately

```bash
docker compose logs api
```

Most common causes:
- **Missing required env var** (`DATABASE_URL`, `SECRET_KEY`) — check your `.env` file.
- **Database not yet healthy** — `start.sh` waits, but increase retries if your DB is slow to start.
- **Port already in use** — run `lsof -i :8000` and kill the conflicting process.

### `uv sync` fails during build

- Ensure `uv.lock` is committed and up-to-date: run `uv lock` then commit the updated lockfile.
- The `--frozen` flag means the lockfile **must** match `pyproject.toml` exactly — any drift causes a build failure.

### Database connection refused

- Confirm the `database` service is healthy: `docker compose ps`.
- Inside the `api` container the hostname must be `database` (the Compose service name), **not** `localhost`.
- Verify `DATABASE_URL` in your env: `postgresql+asyncpg://postgres:postgres@database:5432/app_db`.

### Port 8000 not reachable from outside the host

- Confirm the port binding: `docker compose ps` should show `0.0.0.0:8000->8000/tcp`.
- Check firewall rules on your VM (see Option D in Step 5).
- On cloud providers, verify the Security Group / Firewall allows inbound TCP on port 8000.

### RabbitMQ / Redis connection errors

- In development, set `TASK_QUEUE_USE_IN_MEMORY_BROKER=true` to skip the external broker entirely.
- In full-stack mode, Compose `depends_on: condition: service_healthy` waits for RabbitMQ to be ready before starting `api` and `worker` — if this isn't working, increase the healthcheck `retries` in `docker-compose.yml`.

### Hot-reload not working

- Ensure the source volume mount is present in `docker-compose.yml`: `volumes: - .:/app`.
- Confirm `ENVIRONMENT` is **not** set to `production` — hot-reload is intentionally disabled in production mode by `start.sh`.


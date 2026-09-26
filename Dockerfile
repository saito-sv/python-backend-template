FROM python:3.13-slim

# Install goose for migrations (multi-arch: amd64 or arm64)
ARG GOOSE_VERSION=v3.22.1
ARG TARGETARCH
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && case "${TARGETARCH:-amd64}" in \
         amd64) GOOSE_ARCH="x86_64" ;; \
         arm64) GOOSE_ARCH="arm64" ;; \
         *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
       esac \
    && curl -fsSL "https://github.com/pressly/goose/releases/download/${GOOSE_VERSION}/goose_linux_${GOOSE_ARCH}" \
        -o /usr/local/bin/goose \
    && chmod +x /usr/local/bin/goose \
    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/*

# Pinned to the last validated release; bump tag and digest together.
COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /usr/local/bin/uv

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --compile-bytecode

RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["./start.sh"]

"""Application config, read from environment variables with ``.env`` as fallback.

Each module has its own env prefix. Load only what you need, e.g. ``load("database")``.
"""

import sys
import urllib.parse
from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppConfig(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = "Backend Template"
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


class DatabaseConfig(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    host: str
    port: int = 5432
    name: str
    username: str
    password: str
    echo: bool = False

    @property
    def url(self) -> str:
        """Async SQLAlchemy URL (postgresql+asyncpg)."""
        user = urllib.parse.quote_plus(self.username)
        password = urllib.parse.quote_plus(self.password)
        return f"postgresql+asyncpg://{user}:{password}@{self.host}:{self.port}/{self.name}"

    @property
    def goose_url(self) -> str:
        """Plain PostgreSQL URL for goose (no driver hint)."""
        user = urllib.parse.quote_plus(self.username)
        password = urllib.parse.quote_plus(self.password)
        return f"postgresql://{user}:{password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class RabbitMQConfig(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    host: str = "localhost"
    port: int = 5672
    username: str = "admin"
    password: str = "mypass"
    vhost: str = "/"
    ssl_enabled: bool = False
    exchange_name: str = "taskiq_exchange"
    queue_name: str = "taskiq_queue"

    @property
    def url(self) -> str:
        scheme = "amqps" if self.ssl_enabled else "amqp"
        user = urllib.parse.quote_plus(self.username)
        password = urllib.parse.quote_plus(self.password)
        return f"{scheme}://{user}:{password}@{self.host}:{self.port}{self.vhost}"


class TelemetryConfig(EnvSettings):
    """OpenTelemetry. The standard ``OTEL_EXPORTER_OTLP_*`` env vars configure the exporter."""

    model_config = SettingsConfigDict(env_prefix="OTEL_")

    enabled: bool = False
    service_name: str = "backend-template"
    service_namespace: str | None = None
    """Groups services; Grafana Cloud builds the ``job`` label as ``namespace/name``."""
    log_level: str = "INFO"
    console_exporter: bool = False
    """Print spans to stdout instead of exporting via OTLP (local debugging)."""


class TaskQueueConfig(EnvSettings):
    model_config = SettingsConfigDict(env_prefix="TASK_QUEUE_")

    use_in_memory_broker: bool = True


class Config:
    REGISTRY: ClassVar[Mapping[str, type[BaseSettings]]] = MappingProxyType(
        {
            "app": AppConfig,
            "database": DatabaseConfig,
            "redis": RedisConfig,
            "rabbitmq": RabbitMQConfig,
            "task_queue": TaskQueueConfig,
            "telemetry": TelemetryConfig,
        }
    )

    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    rabbitmq: RabbitMQConfig
    task_queue: TaskQueueConfig
    telemetry: TelemetryConfig

    def __init__(self, modules: list[str] | None = None) -> None:
        for name in modules or list(self.REGISTRY):
            if name not in self.REGISTRY:
                raise ValueError(f"Unknown config module: {name}")
            setattr(self, name, self.REGISTRY[name]())


def load(*modules: str) -> Config:
    """Load the given config modules (all of them if none are given)."""
    try:
        return Config(list(modules) if modules else None)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

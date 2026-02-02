from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Backend Template"
    debug: bool = False
    environment: str = "development"
    run_migrations_on_startup: bool = False

    # Database
    database_url: PostgresDsn
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ (for TaskIQ)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


# Global settings instance
settings = Settings()

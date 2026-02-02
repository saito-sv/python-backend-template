from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    host: str = "redis"
    port: int = 6379
    password: str | None = None
    db: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        extra="ignore",
    )

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


REDIS_SETTINGS = RedisSettings()

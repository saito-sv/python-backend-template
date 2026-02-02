from pydantic_settings import BaseSettings, SettingsConfigDict


class TaskQueueSettings(BaseSettings):
    use_in_memory_broker: bool = False
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TASK_QUEUE_",
        extra="ignore",
    )


TASK_QUEUE_SETTINGS = TaskQueueSettings()

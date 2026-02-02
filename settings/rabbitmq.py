from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    host: str = "rabbitmq"
    port: int = 5672
    username: str = "admin"
    password: str = "mypass"
    vhost: str = "/"
    ssl_enabled: bool = False
    exchange_name: str = "taskiq_exchange"
    queue_name: str = "taskiq_queue"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RABBITMQ_",
        extra="ignore",
    )

    @property
    def url(self) -> str:
        return self.build_amqp_url(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            vhost=self.vhost,
            ssl_enabled=self.ssl_enabled,
        )

    @staticmethod
    def build_amqp_url(
        host: str,
        port: int,
        username: str,
        password: str,
        vhost: str = "/",
        ssl_enabled: bool = False,
    ) -> str:
        scheme = "amqps" if ssl_enabled else "amqp"
        return f"{scheme}://{username}:{password}@{host}:{port}{vhost}"


RABBITMQ_SETTINGS = RabbitMQSettings()

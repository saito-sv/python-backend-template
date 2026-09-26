from app.telemetry import setup_telemetry

# The worker imports this module first, so telemetry is configured before tasks run.
setup_telemetry()

from taskiq import AsyncBroker, InMemoryBroker  # noqa: E402
from taskiq.middlewares.opentelemetry_middleware import OpenTelemetryMiddleware  # noqa: E402
from taskiq.serializers import ORJSONSerializer  # noqa: E402
from taskiq_aio_pika import AioPikaBroker  # noqa: E402
from taskiq_redis import RedisAsyncResultBackend  # noqa: E402

from app.config import load  # noqa: E402

_cfg = load("task_queue", "redis", "rabbitmq", "telemetry")


def _create_production_broker() -> AsyncBroker:
    result_backend = RedisAsyncResultBackend(_cfg.redis.url)

    return AioPikaBroker(
        url=_cfg.rabbitmq.url,
        exchange_name=_cfg.rabbitmq.exchange_name,
        queue_name=_cfg.rabbitmq.queue_name,
        declare_exchange=True,
    ).with_result_backend(result_backend)


def _create_broker() -> AsyncBroker:
    if _cfg.task_queue.use_in_memory_broker:
        base_broker = InMemoryBroker()
    else:
        base_broker = _create_production_broker()

    broker = base_broker.with_serializer(ORJSONSerializer())
    if _cfg.telemetry.enabled:
        # Propagates trace context from the enqueuing request into the task's span.
        broker = broker.with_middlewares(OpenTelemetryMiddleware())
    return broker


broker = _create_broker()

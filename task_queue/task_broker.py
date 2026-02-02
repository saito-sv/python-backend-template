from taskiq import AsyncBroker, InMemoryBroker
from taskiq.serializers import ORJSONSerializer
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from settings.rabbitmq import RABBITMQ_SETTINGS
from settings.redis import REDIS_SETTINGS
from task_queue.settings import TASK_QUEUE_SETTINGS


def _create_production_broker() -> AsyncBroker:
    result_backend = RedisAsyncResultBackend(REDIS_SETTINGS.url)

    broker = AioPikaBroker(
        url=RABBITMQ_SETTINGS.url,
        exchange_name=RABBITMQ_SETTINGS.exchange_name,
        queue_name=RABBITMQ_SETTINGS.queue_name,
        declare_exchange=True,
    ).with_result_backend(result_backend)

    return broker


def _create_broker() -> AsyncBroker:
    if TASK_QUEUE_SETTINGS.use_in_memory_broker:
        base_broker = InMemoryBroker()
    else:
        base_broker = _create_production_broker()

    return base_broker.with_serializer(ORJSONSerializer())


broker = _create_broker()

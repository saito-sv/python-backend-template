from contextlib import asynccontextmanager

from taskiq import AsyncBroker


async def start_task_broker(broker: AsyncBroker) -> None:
    """Start the task broker only if not running in worker process.

    This prevents double-initialization when the same process acts as both
    API server and worker.
    """
    if not broker.is_worker_process:
        await broker.startup()


async def stop_task_broker(broker: AsyncBroker) -> None:
    """Stop the task broker only if not running in worker process.

    This ensures proper cleanup without interfering with worker process shutdown.
    """
    if not broker.is_worker_process:
        await broker.shutdown()


@asynccontextmanager
async def broker_context(broker: AsyncBroker):
    """Context manager for broker lifecycle management."""
    await start_task_broker(broker)
    try:
        yield
    finally:
        await stop_task_broker(broker)

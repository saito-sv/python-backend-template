from taskiq import AsyncBroker


async def start_task_broker(broker: AsyncBroker) -> None:
    """Start the broker for enqueueing. Worker processes manage their own lifecycle."""
    if not broker.is_worker_process:
        await broker.startup()


async def stop_task_broker(broker: AsyncBroker) -> None:
    if not broker.is_worker_process:
        await broker.shutdown()

"""TaskIQ worker entry point (``taskiq worker task_queue.worker:broker``)."""

from taskiq import TaskiqEvents, TaskiqState

from app.telemetry import shutdown_telemetry
from task_queue.task_broker import broker


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def _flush_telemetry(_: TaskiqState) -> None:
    # Spans are batched; flush them so the last tasks before a deploy aren't lost.
    shutdown_telemetry()


__all__ = ["broker"]

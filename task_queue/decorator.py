from collections.abc import Awaitable, Callable
from typing import Any, overload

from taskiq import AsyncTaskiqDecoratedTask

from task_queue.task_broker import broker

type _TaskDecorator[**P, R] = Callable[[Callable[P, R]], AsyncTaskiqDecoratedTask[P, R]]


@overload
def task[**P, R: Awaitable](func: Callable[P, R]) -> AsyncTaskiqDecoratedTask[P, R]: ...


@overload
def task[**P, R: Awaitable](
    *,
    schedule: list[dict[str, Any]] | None = None,
    task_name: str | None = None,
) -> _TaskDecorator[P, R]: ...


def task[**P, R: Awaitable](
    func: Callable[P, R] | None = None,
    *,
    schedule: list[dict[str, Any]] | None = None,
    task_name: str | None = None,
) -> AsyncTaskiqDecoratedTask[P, R] | _TaskDecorator[P, R]:
    """Register an async function as a background task.

    Usable bare (``@task``) or with options (``@task(schedule=[{"cron": "0 2 * * *"}])``).
    The task name defaults to ``module:function``. Enqueue with ``await my_task.kiq(...)``.
    """

    def decorator(func: Callable[P, R]) -> AsyncTaskiqDecoratedTask[P, R]:
        labels: dict[str, Any] = {} if schedule is None else {"schedule": schedule}
        name = task_name or f"{func.__module__}:{func.__name__}"

        @broker.task(task_name=name, **labels)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper  # pyright: ignore[reportReturnType]

    return decorator(func) if func is not None else decorator

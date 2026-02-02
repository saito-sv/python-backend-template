from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, overload

from taskiq import AsyncTaskiqDecoratedTask

from task_queue.task_broker import broker

_FuncParams = ParamSpec("_FuncParams")
_ReturnType = TypeVar("_ReturnType", bound=Awaitable)


@overload
def task[**FuncParams, ReturnType: Awaitable](
    func: Callable[FuncParams, ReturnType] | None,
) -> AsyncTaskiqDecoratedTask[FuncParams, ReturnType]: ...


@overload
def task(
    *,
    schedule: list[dict[str, Any]] | None = None,
    task_name: str | None = None,
) -> Callable[
    [Callable[_FuncParams, _ReturnType]],
    AsyncTaskiqDecoratedTask[_FuncParams, _ReturnType],
]: ...


def task[**FuncParams, ReturnType: Awaitable](
    func: Callable[FuncParams, ReturnType] | None = None,
    *,
    schedule: list[dict[str, Any]] | None = None,
    task_name: str | None = None,
) -> (
    AsyncTaskiqDecoratedTask[FuncParams, ReturnType]
    | Callable[
        [Callable[FuncParams, ReturnType]],
        AsyncTaskiqDecoratedTask[FuncParams, ReturnType],
    ]
):
    """
    A decorator to register background tasks with TaskIQ.

    Usage:
        @task
        async def my_task(arg1: str, arg2: int):
            # Task logic here
            pass

        # Enqueue the task
        await my_task.kiq(arg1="value", arg2=42)

    :param func: The function to be decorated.
    :param schedule: Optional list of dictionaries specifying cron schedules.
    :param task_name: Optional custom task name.
    :return: The decorated task.
    """

    def decorator(
        func: Callable[FuncParams, ReturnType],
    ) -> AsyncTaskiqDecoratedTask[FuncParams, ReturnType]:
        use_task_name = task_name or f"{func.__module__}:{func.__name__}"

        if schedule is not None:
            task_decorator = broker.task(task_name=use_task_name, schedule=schedule)
        else:
            task_decorator = broker.task(task_name=use_task_name)

        @task_decorator
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper  # pyright: ignore[reportReturnType]

    if func is not None:
        return decorator(func)

    return decorator

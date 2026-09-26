"""Antidote injection for FastAPI route handlers.

FastAPI would treat ``inject.me()`` defaults as request parameters. ``@hidden_inject``
removes injected parameters from the visible signature while antidote still resolves
them at call time. Async handlers only.

    @router.get("/items")
    @hidden_inject
    async def list_items(service: ItemService = inject.me()) -> list[ItemRead]: ...
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any

from antidote import ParameterDependency, inject, world


def hidden_inject[F: Callable](func: F) -> F:
    if not inspect.iscoroutinefunction(func):
        name = getattr(func, "__name__", repr(func))
        raise TypeError(f"@hidden_inject requires an async function; '{name}' is sync.")

    injected = inject(func, app_catalog=world)

    signature = inspect.signature(func)
    visible_params = [
        p for p in signature.parameters.values() if not isinstance(p.default, ParameterDependency)
    ]

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await injected(*args, **kwargs)

    wrapper.__signature__ = signature.replace(parameters=visible_params)  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]

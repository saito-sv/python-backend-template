"""
A wrapper around antidote's inject that works for FastAPI routers and dependencies
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from antidote import ParameterDependency, inject

F = TypeVar("F", bound=Callable)


def hidden_inject[F: Callable](func: F) -> F:
    """
    A wrapper around antidote's inject that works for FastAPI routers and dependencies

    This works by modifying the function's revealed signature at runtime to exclude the injected parameters.
    It does not actually affect the behavior of the function other than injecting: you can still manually
    pass the parameters. Those parameters will just be hidden from any tool that tries to examine type
    annotations at runtime, such as FastAPI.

    It is still preferred to use the native inject if possible. Only use this for FastAPI routers and dependencies.
    """
    injected_func = inject(func)

    @wraps(injected_func)
    async def async_wrapper(*args, **kwargs):
        return await injected_func(*args, **kwargs)

    @wraps(injected_func)
    def sync_wrapper(*args, **kwargs):
        return injected_func(*args, **kwargs)

    wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    # Filter out injected parameters
    non_injected_params = {
        k: v
        for k, v in inspect.signature(func).parameters.items()
        if not isinstance(v.default, ParameterDependency)
    }

    # Update the wrapper function's signature
    wrapper.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        parameters=list(non_injected_params.values())
    )

    return wrapper  # type: ignore[return-value]

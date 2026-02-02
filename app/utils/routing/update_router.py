"""Utility to update router route classes."""

from typing import TypeVar

from fastapi import APIRouter
from fastapi.routing import APIRoute

Route = TypeVar("Route", bound=APIRoute)


def update_router_route_class[Route: APIRoute](router: APIRouter, route_cls: type[Route]):
    """Update all routes in a router to use a custom route class.

    This is needed to apply custom logging to routers we don't control,
    such as those from third-party libraries.

    Args:
        router: The FastAPI router to update
        route_cls: The custom route class to apply (e.g., LoggedRoute)

    Example:
        from app.utils.routing.request_log import LoggedRoute
        from app.utils.routing.update_router import update_router_route_class

        router = APIRouter()
        # ... add routes ...
        update_router_route_class(router, LoggedRoute)
    """
    router.route_class = route_cls
    for route in router.routes:
        route.__class__ = route_cls

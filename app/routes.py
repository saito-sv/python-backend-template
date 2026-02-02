"""Central router configuration for the application."""

from collections.abc import Sequence

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict

from app.domains.post.router import router as post_router
from app.domains.user.router import router as user_router
from app.utils.routing.request_log import LoggedRoute
from app.utils.routing.update_router import update_router_route_class


class RouteConfig(BaseModel):
    """Configuration for a router to be included in the application.

    This class wraps router configuration with metadata and applies
    custom route classes for consistent logging and behavior.

    Attributes:
        router: The FastAPI router to include
        prefix: URL prefix for all routes in this router
        tags: OpenAPI tags for documentation
        route_class: Custom route class to apply (default: LoggedRoute)

    Example:
        config = RouteConfig(
            router=users_router,
            prefix="/users",
            tags=["users"],
        )
        config.configure(app)
    """

    router: APIRouter
    prefix: str
    tags: Sequence[str]
    route_class: type[APIRoute] = LoggedRoute

    def configure(self, app: FastAPI):
        """Apply this configuration to a FastAPI app.

        This method:
        1. Updates the router to use the custom route class
        2. Includes the router in the app with the specified prefix and tags

        Args:
            app: The FastAPI application to configure
        """
        update_router_route_class(self.router, self.route_class)
        app.include_router(
            self.router,
            prefix=self.prefix,
            tags=list(self.tags),
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


def _create_route_configs() -> list[RouteConfig]:
    """Create the list of route configurations for the application.

    Add new routers here as you create new domains.

    Returns:
        List of RouteConfig objects to be applied to the app
    """
    route_configs = [
        RouteConfig(
            router=user_router,
            prefix="/user",
            tags=["user"],
        ),
        RouteConfig(
            router=post_router,
            prefix="/post",
            tags=["post"],
        ),
    ]

    return route_configs


def add_routers(app: FastAPI):
    """Add all configured routers to the FastAPI application.

    This function applies all route configurations defined in
    _create_route_configs() to the given FastAPI app.

    Args:
        app: The FastAPI application to configure

    Example:
        app = FastAPI()
        add_routers(app)
    """
    for route_config in _create_route_configs():
        route_config.configure(app)

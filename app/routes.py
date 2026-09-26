"""Router registration.

Each domain's ``router.py`` exposes a module-level ``route_config``. Every domain under
``app.domains`` is discovered and mounted under ``API_PREFIX``; no manual list to update.
"""

import importlib
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, ConfigDict

API_PREFIX: Final = "/v1"
DOMAINS_PACKAGE: Final = "app.domains"


class RouteConfig(BaseModel):
    """Declare in a domain's ``router.py``:

    route_config = RouteConfig(router=router, prefix="/users", tags=["users"])
    """

    router: APIRouter
    prefix: str
    tags: Sequence[str]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def configure(self, app: FastAPI) -> None:
        app.include_router(self.router, prefix=f"{API_PREFIX}{self.prefix}", tags=list(self.tags))


def _discover_route_configs() -> list[RouteConfig]:
    pkg = importlib.import_module(DOMAINS_PACKAGE)
    configs: list[RouteConfig] = []
    for base in pkg.__path__:
        for router_file in sorted(Path(base).glob("*/router.py")):
            module = importlib.import_module(f"{DOMAINS_PACKAGE}.{router_file.parent.name}.router")
            config = getattr(module, "route_config", None)
            if isinstance(config, RouteConfig):
                configs.append(config)
    return configs


def add_routers(app: FastAPI) -> None:
    for route_config in _discover_route_configs():
        route_config.configure(app)

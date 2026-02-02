"""Request logging for API routes."""

import logging
import timeit
from collections.abc import Callable
from json import JSONDecodeError

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


class LoggedRoute(APIRoute):
    """Custom APIRoute that logs all requests and responses.

    This route class wraps the standard FastAPI route handler to add:
    - Request/response logging with timing
    - Error logging with status codes
    - JSON request body parsing

    Example:
        router = APIRouter(route_class=LoggedRoute)

        @router.get("/users")
        async def get_users():
            return {"users": []}
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = timeit.default_timer()

            async def log_info(
                message: str,
                request_json: dict | None,
                resp_or_err: Response | Exception,
            ):
                duration = timeit.default_timer() - before
                url = f"{request.url.path}{'?' + request.url.query if request.url.query else ''}"
                full_message = f"{request.method} {url} {message} - {duration:.3f}s"
                logger.info(full_message)

            request_json = await _safe_request_json(request)
            try:
                response: Response = await original_route_handler(request)

            except HTTPException as e:
                await log_info(f"{e.status_code} - {e.detail}", request_json, e)
                raise e
            except RequestValidationError as e:
                await log_info(f"422 - Validation Error: {e}", request_json, e)
                raise e
            except Exception as e:
                await log_info(f"500 - Internal Server Error: {e}", request_json, e)
                raise e

            await log_info(f"{response.status_code}", request_json, response)
            return response

        return custom_route_handler


async def _safe_request_json(request: Request) -> dict | None:
    """Safely parse request JSON, returning None if parsing fails."""
    try:
        return await request.json()
    except JSONDecodeError:
        return None

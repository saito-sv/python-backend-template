from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.exc import ClientException, DuplicateEntityException, ForeignKeyViolationException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ClientException)
    async def client_exception_handler(_: Request, exc: ClientException) -> JSONResponse:
        return exc.to_http_response()

    @app.exception_handler(DuplicateEntityException)
    async def duplicate_entity_handler(_: Request, __: DuplicateEntityException) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Entity already exists."})

    @app.exception_handler(ForeignKeyViolationException)
    async def foreign_key_violation_handler(
        _: Request, __: ForeignKeyViolationException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409, content={"detail": "Foreign key constraint violation."}
        )

"""Application exception hierarchy."""

import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Final

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import SQLModel
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from app.repository.filter import DataFilter

_UNIQUE_CONSTRAINT_NAME_RE: Final = re.compile(r"violates unique constraint \"([^\"]+)\"")


class BackendException(Exception):
    pass


class DatabaseException(BackendException):
    pass


class DuplicateEntityException(DatabaseException):
    """Unique constraint violation, mapped from the database error."""

    def __init__(self, cause: Exception) -> None:
        message = str(cause)
        super().__init__(message)
        match = _UNIQUE_CONSTRAINT_NAME_RE.search(message)
        self.constraint_violation_name: str | None = match.group(1) if match else None


class ForeignKeyViolationException(DatabaseException):
    pass


class MultipleEntitiesWhenOneRequestedException(DatabaseException):
    pass


class RepositoryUsageException(BackendException):
    pass


class ClientException(BackendException):
    """Error that is safe to expose to API clients, with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400):
        self.status_code = status_code
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail=str(self))

    def to_http_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content={"detail": str(self)})


class DatabaseClientException(ClientException, DatabaseException):
    pass


class EntityExistsException(DatabaseClientException):
    def __init__(self, message: str = "Entity already exists"):
        super().__init__(message, status_code=409)


class EntityNotFoundException(DatabaseClientException):
    def __init__[T: SQLModel](
        self,
        entity_db_type: type[T],
        id: str | None = None,
        filters: "Sequence[DataFilter[T] | None] | None" = None,
        extra_message: str | None = None,
    ):
        self.entity_db_type = entity_db_type
        self.id = id
        self.filters = filters

        message = f"{entity_db_type.__name__} not found"
        if id is not None:
            message += f" with id {id}"
        if filters is not None:
            message += f" with filters {list(filters)}"
        if extra_message is not None:
            message += f". {extra_message}"
        super().__init__(message, status_code=404)


class ClientValidationException(ClientException):
    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        super().__init__(str(validation_error), status_code=422)

    def to_http_response(self) -> JSONResponse:
        # Context is excluded because it can contain non-serializable objects.
        return JSONResponse(
            status_code=self.status_code,
            content={"detail": self.validation_error.errors(include_context=False)},
        )


class NotSupportedException(ClientException):
    def __init__(self, message: str = "Not supported"):
        super().__init__(message, status_code=501)

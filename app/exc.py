"""Common exception classes for the application."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar

from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import SQLModel
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from app.repository.filter import DataFilter

T = TypeVar("T", bound=SQLModel)


class BackendException(Exception):
    """Base exception for all backend errors."""

    pass


class DatabaseException(BackendException):
    """Base exception for database-related errors."""

    pass


class ClientException(BackendException):
    """Base exception for client-facing errors with HTTP status codes."""

    def __init__(self, message: str, status_code: int = 400):
        self.status_code = status_code
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(status_code=self.status_code, detail=str(self))

    def to_http_response(self) -> JSONResponse:
        """Convert to Starlette JSONResponse."""
        return JSONResponse(status_code=self.status_code, content={"detail": str(self)})


class DatabaseClientException(ClientException, DatabaseException):
    """Exception for database errors that should be exposed to clients."""

    pass


class RepositoryUsageException(BackendException):
    """Exception for incorrect repository usage."""

    pass


class EntityExistsException(DatabaseClientException):
    """Exception raised when attempting to create an entity that already exists."""

    pass


class EntityNotFoundException(DatabaseClientException):
    """Exception raised when an entity is not found in the database."""

    def __init__(
        self,
        entity_db_type: type[T],
        id: str | None = None,
        filters: Sequence["DataFilter[T] | None"] | None = None,
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


class MultipleEntitiesWhenOneRequestedException(DatabaseException):
    """Exception raised when multiple entities are found but only one was expected."""

    pass


class ClientValidationException(ClientException):
    """Exception for Pydantic validation errors."""

    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        super().__init__(str(validation_error), status_code=422)

    def to_http_response(self) -> JSONResponse:
        """Convert to Starlette JSONResponse with validation error details."""
        return JSONResponse(
            status_code=self.status_code,
            content={
                "detail": self.validation_error.errors(
                    include_context=False  # Do not include context as it can contain un-serializable objects
                )
            },
        )


class NotSupportedException(ClientException):
    """Exception for unsupported operations."""

    def __init__(self, message: str = "Not supported"):
        super().__init__(message, status_code=501)

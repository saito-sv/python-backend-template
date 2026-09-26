"""Base classes for table models: prefixed ULID ids, timestamps and soft delete.

Column constraints and defaults are defined in the goose migrations, not here.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, ClassVar, Final

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel
from ulid import ULID

_ULID_CHAR_LENGTH: Final = 26


def random_object_id_factory(prefix: str) -> Callable[[], str]:
    """Return a factory producing ids like ``usr_01j9z3k6v7f8g9h0j1k2m3n4p5``."""

    def object_id() -> str:
        return f"{prefix}_{str(ULID()).lower()}"

    return object_id


def utcnow() -> datetime:
    return datetime.now(UTC)


_TIMESTAMPTZ: Final[Any] = DateTime(timezone=True)


def _TimestampField(default_now: bool) -> Any:
    if default_now:
        return Field(default_factory=utcnow, sa_type=_TIMESTAMPTZ)
    return Field(default=None, sa_type=_TIMESTAMPTZ)


class CreatedAtMixin(SQLModel):
    created_at: datetime = _TimestampField(default_now=True)


class UpdatedAtMixin(SQLModel):
    updated_at: datetime = _TimestampField(default_now=True)


class DeletedAtMixin(SQLModel):
    deleted_at: datetime | None = _TimestampField(default_now=False)


class BaseSQLModel(CreatedAtMixin, UpdatedAtMixin, DeletedAtMixin, SQLModel):
    pass


class BaseObjectIdSQLModel(BaseSQLModel):
    id: str | None


def IDTableModelMixinFactory(prefix: str) -> type[SQLModel]:
    class IDTableModelMixin(SQLModel):
        _prefix: ClassVar[str] = prefix
        id: str | None = Field(
            default_factory=random_object_id_factory(prefix),
            primary_key=True,
            regex=f"^{prefix}_[0-9a-z]{{{_ULID_CHAR_LENGTH}}}$",
        )

    return IDTableModelMixin


def BaseIDTableModelFactory(prefix: str) -> type[BaseObjectIdSQLModel]:
    """Base for table models: ``id``, ``created_at``, ``updated_at`` and ``deleted_at``.

    Example:
        class User(UserBase, BaseIDTableModelFactory("usr"), table=True):
            __tablename__ = "users"
    """
    IDTableMixin = IDTableModelMixinFactory(prefix)

    class BaseIDSQLModel(  # pyright: ignore[reportGeneralTypeIssues]
        IDTableMixin, BaseSQLModel
    ):
        pass

    return BaseIDSQLModel  # pyright: ignore[reportReturnType]

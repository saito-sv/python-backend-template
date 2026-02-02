"""Base model classes for database models."""

import random
from collections.abc import Callable
from datetime import UTC, datetime
from string import ascii_lowercase, digits
from typing import Any, ClassVar

from sqlmodel import Field, SQLModel

from app.utils.schemas import DatetimeSerializeAsUTC

_id_char_length = 32


def _random_id_string(length: int) -> str:
    """Generate a random string of lowercase letters and digits."""
    return "".join(random.choice(ascii_lowercase + digits) for _ in range(length))


def random_object_id_factory(prefix: str, length: int = _id_char_length) -> Callable[[], str]:
    """Create a factory function that generates random object IDs with a prefix.

    Args:
        prefix: The prefix for the ID (e.g., "usr", "prd")
        length: The length of the random string portion (default: 32)

    Returns:
        A factory function that generates IDs like "usr_abc123..."
    """

    def random_object_id() -> str:
        return f"{prefix}_{_random_id_string(length)}"

    return random_object_id


def naive_utcnow() -> datetime:
    """Get current UTC time as naive datetime."""
    return datetime.now(UTC).replace(tzinfo=None)


def DateNowField() -> Any:
    """Create a Field with current UTC timestamp as default."""
    return Field(
        default_factory=naive_utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": "now()"},
    )


class CreatedAtMixin(SQLModel):
    """Mixin for created_at timestamp."""

    created_at: DatetimeSerializeAsUTC = DateNowField()


class UpdatedAtMixin(SQLModel):
    """Mixin for updated_at timestamp."""

    updated_at: DatetimeSerializeAsUTC = DateNowField()


class BaseSQLModel(CreatedAtMixin, UpdatedAtMixin, SQLModel):
    """Base model with created_at and updated_at timestamps."""

    pass


class BaseObjectIdSQLModel(BaseSQLModel):
    """Base model with object ID.

    Note: For typing purposes, use BaseIDTableModelFactory for subclassing.
    """

    id: str | None


_observed_prefixes: set[str] = set()


def IDTableModelMixinFactory(prefix: str) -> type[SQLModel]:
    """Create a mixin class that adds an ID field with the given prefix.

    Args:
        prefix: The prefix for the ID (e.g., "usr", "prd")

    Returns:
        A mixin class with an ID field

    Raises:
        ValueError: If the prefix has already been used
    """
    global _observed_prefixes
    if prefix in _observed_prefixes:
        raise ValueError(
            f"Prefix {prefix} already observed. Did you choose a unique prefix for "
            + "IDTableModelMixinFactory/BaseIDTableModelFactory?"
        )
    _observed_prefixes.add(prefix)

    class IDTableModelMixin(SQLModel):
        _prefix: ClassVar[str] = prefix
        id: str | None = Field(
            default_factory=random_object_id_factory(prefix),
            primary_key=True,
            nullable=False,
            regex=f"^{prefix}_[a-z0-9]{{{_id_char_length}}}$",
        )

    return IDTableModelMixin


def BaseIDTableModelFactory(prefix: str) -> type[BaseObjectIdSQLModel]:
    """Create a base model class with ID, created_at, and updated_at fields.

    This is the recommended way to create domain models.

    Args:
        prefix: The prefix for the ID (e.g., "usr", "prd")

    Returns:
        A base model class that can be used for table inheritance

    Example:
        ```python
        ID_PREFIX = "usr"

        class User(BaseIDTableModelFactory(ID_PREFIX), table=True):
            email: str = Field(unique=True, index=True)
            full_name: str | None = None
        ```
    """
    IDTableMixin = IDTableModelMixinFactory(prefix)

    class BaseIDSQLModel(  # pyright: ignore[reportGeneralTypeIssues]
        IDTableMixin, BaseSQLModel
    ):
        pass

    return BaseIDSQLModel  # pyright: ignore[reportReturnType]


class BaseRead(SQLModel):
    """Base read schema with id and timestamps."""

    id: str
    created_at: DatetimeSerializeAsUTC
    updated_at: DatetimeSerializeAsUTC

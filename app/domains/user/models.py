"""User database models: the table mapping and the shapes the repository writes.

Columns only; constraints and defaults live in the goose migration.
"""

from sqlmodel import SQLModel

from app.database.model_base import BaseIDTableModelFactory

from .constants import USER_ID_PREFIX


class UserBase(SQLModel):
    email: str
    full_name: str | None = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, BaseIDTableModelFactory(USER_ID_PREFIX), table=True):
    __tablename__ = "users"  # type: ignore[assignment]


class UserDBCreate(SQLModel):
    """Insert shape; the password is already hashed."""

    email: str
    full_name: str | None = None
    hashed_password: str


class UserDBUpdate(SQLModel):
    """Update shape; the password is already hashed."""

    email: str | None = None
    full_name: str | None = None
    hashed_password: str | None = None
    is_active: bool | None = None

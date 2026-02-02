"""User database models and schemas for repository layer."""

from sqlmodel import Field, SQLModel

from app.database.model_base import BaseIDTableModelFactory, BaseRead

ID_PREFIX = "usr"


class UserBase(SQLModel):
    """Base user fields shared across schemas."""

    email: str
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, BaseIDTableModelFactory(ID_PREFIX), table=True):
    """User database model."""

    __tablename__ = "users"

    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)


class UserCreate(UserBase):
    """Schema for creating a user in the repository."""

    hashed_password: str


class UserUpdate(SQLModel):
    """Schema for updating a user in the repository."""

    email: str | None = None
    hashed_password: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserRead(UserBase, BaseRead):
    """Schema for reading a user from the repository."""

    pass

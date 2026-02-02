"""User API schemas for external API."""

from pydantic import BaseModel, EmailStr

from app.domains.user.models import UserRead


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user via API."""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user via API."""

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None


__all__ = ["UserBase", "UserCreate", "UserUpdate", "UserRead"]

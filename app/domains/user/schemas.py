"""User API schemas (request/response types)."""

from typing import Annotated, Final

from pydantic import AfterValidator, BaseModel, Field

from app.utils.schemas import BaseRead, NormalizedEmail

_BCRYPT_MAX_BYTES: Final = 72


def _fits_bcrypt(value: str) -> str:
    if len(value.encode()) > _BCRYPT_MAX_BYTES:
        raise ValueError(f"must be at most {_BCRYPT_MAX_BYTES} bytes")
    return value


# bcrypt only uses the first 72 bytes (and bcrypt>=5 raises beyond that), so cap it here.
Password = Annotated[str, Field(min_length=8), AfterValidator(_fits_bcrypt)]


class UserRead(BaseRead):
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool


class UserCreate(BaseModel):
    email: NormalizedEmail
    full_name: str | None = None
    password: Password


class UserUpdate(BaseModel):
    email: NormalizedEmail | None = None
    full_name: str | None = None
    password: Password | None = None
    is_active: bool | None = None

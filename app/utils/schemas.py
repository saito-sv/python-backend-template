import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    PlainSerializer,
)


class TemplateModel(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)


def _strip_timezone(v: datetime.datetime) -> datetime.datetime:
    if v.tzinfo:
        return v.astimezone(datetime.UTC).replace(tzinfo=None)
    return v


NaiveDatetime = Annotated[datetime.datetime, AfterValidator(_strip_timezone)]

DatetimeSerializeAsUTC = Annotated[
    NaiveDatetime,
    PlainSerializer(
        lambda v: v.replace(tzinfo=datetime.UTC) if v.tzinfo is None else v,
        return_type=NaiveDatetime,
        when_used="json-unless-none",
    ),
]


def _normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


NormalizedEmail = Annotated[EmailStr, BeforeValidator(_normalize_email)]


class BaseRead(BaseModel):
    """Base response model: id plus UTC-serialized timestamps. Validates from ORM objects."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: DatetimeSerializeAsUTC
    updated_at: DatetimeSerializeAsUTC


ObjectId = Annotated[str, Field(pattern=r"^[a-z]+_[0-9a-z]{26}$")]
"""A prefixed ULID, e.g. ``usr_01j9z3k6v7f8g9h0j1k2m3n4p5``."""


class CursorParams(BaseModel):
    """Keyset pagination over ULID ids (which sort by creation time).

    Pass the previous page's ``next_cursor`` as ``cursor`` to get the next page.
    """

    cursor: ObjectId | None = None
    limit: int = Field(default=50, ge=1, le=200)
    order: Literal["asc", "desc"] = "desc"


class CursorPage[T](BaseModel):
    items: list[T]
    next_cursor: str | None
    """Id of the last item when more results exist; ``None`` on the last page."""

"""Post API schemas (request/response types)."""

from pydantic import BaseModel, Field

from app.utils.schemas import BaseRead


class PostRead(BaseRead):
    user_id: str
    title: str
    content: str


class PostCreate(BaseModel):
    user_id: str
    title: str = Field(max_length=200)
    content: str


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None

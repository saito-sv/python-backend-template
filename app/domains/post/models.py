"""Post database models. Columns only; constraints and defaults live in the goose migration."""

from sqlmodel import Field, SQLModel

from app.database.model_base import BaseIDTableModelFactory

from .constants import POST_ID_PREFIX


class PostBase(SQLModel):
    user_id: str = Field(foreign_key="users.id")
    title: str
    content: str


class Post(PostBase, BaseIDTableModelFactory(POST_ID_PREFIX), table=True):
    __tablename__ = "posts"  # type: ignore[assignment]

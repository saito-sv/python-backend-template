from sqlmodel import Field, SQLModel

from app.database.model_base import BaseIDTableModelFactory, BaseRead

ID_PREFIX = "pst"


class PostBase(SQLModel):
    title: str
    content: str
    user_id: str


class Post(PostBase, BaseIDTableModelFactory(ID_PREFIX), table=True):
    __tablename__ = "posts"

    title: str = Field(max_length=200, nullable=False)
    content: str = Field(nullable=False)
    user_id: str = Field(index=True, nullable=False)


class PostCreate(PostBase):
    pass


class PostUpdate(SQLModel):
    title: str | None = None
    content: str | None = None


class PostRead(PostBase, BaseRead):
    pass

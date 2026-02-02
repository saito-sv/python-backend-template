from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    user_id: str


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class PostResponse(BaseModel):
    id: str
    title: str
    content: str
    user_id: str
    created_at: str
    updated_at: str

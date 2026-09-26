"""Post repository."""

from dataclasses import dataclass
from typing import Any

from antidote import injectable

from app.repository.base import MainObjectIdRepository
from app.repository.filter import DataFilter
from app.utils.schemas import CursorPage, CursorParams

from .models import Post
from .schemas import PostCreate, PostRead, PostUpdate


@dataclass
class _UserIdFilter(DataFilter[Post]):
    user_id: str

    @property
    def expression(self) -> Any:
        return Post.user_id == self.user_id


@injectable(lifetime="transient")
class PostRepository(MainObjectIdRepository[PostCreate, PostRead, PostUpdate, Post]):
    _db_class = Post
    _read_class = PostRead

    @staticmethod
    def user_id_filter(user_id: str) -> DataFilter[Post]:
        return _UserIdFilter(user_id)

    async def list_for_user(self, user_id: str, params: CursorParams) -> CursorPage[PostRead]:
        return await self.paginate(
            self.user_id_filter(user_id),
            cursor=params.cursor,
            limit=params.limit,
            order=params.order,
        )

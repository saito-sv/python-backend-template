from dataclasses import dataclass
from typing import Any, override

from antidote import injectable

from app.domains.post.models import Post, PostCreate, PostRead, PostUpdate
from app.repository.base import MainObjectIdRepository
from app.repository.filter import DataFilter


@dataclass
class _UserIdFilter(DataFilter[Post]):
    user_id: str

    @property
    @override
    def expression(self) -> Any:
        return Post.user_id == self.user_id


@injectable(lifetime="transient")
class PostRepository(MainObjectIdRepository[PostCreate, PostRead, PostUpdate, Post]):
    _db_class = Post
    _read_class = PostRead

    @staticmethod
    def user_id_filter(user_id: str) -> _UserIdFilter:
        return _UserIdFilter(user_id)

"""Post domain service."""

from antidote import inject, injectable

from app.domains.user.service import UserService
from app.utils.schemas import CursorPage, CursorParams

from .repository import PostRepository
from .schemas import PostCreate, PostRead, PostUpdate


@injectable
class PostService:
    @inject
    def __init__(
        self,
        post_repo: PostRepository = inject.me(),
        user_service: UserService = inject.me(),
    ) -> None:
        self._post_repo = post_repo
        self._user_service = user_service

    async def create_post(self, data: PostCreate) -> PostRead:
        await self._user_service.get_user(data.user_id)
        return await self._post_repo.create(data)

    async def get_post(self, post_id: str) -> PostRead:
        return await self._post_repo.get_by_id_or_raise(post_id)

    async def list_posts_for_user(self, user_id: str, params: CursorParams) -> CursorPage[PostRead]:
        return await self._post_repo.list_for_user(user_id, params)

    async def update_post(self, post_id: str, data: PostUpdate) -> PostRead:
        return await self._post_repo.update_by_id(data, post_id)

    async def delete_post(self, post_id: str) -> None:
        await self._post_repo.delete_by_id(post_id)

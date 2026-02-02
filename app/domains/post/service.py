from dataclasses import dataclass

from antidote import inject, injectable

from app.domains.post.models import PostCreate, PostRead, PostUpdate
from app.domains.post.repository import PostRepository
from app.domains.post.schemas import PostCreate as ApiPostCreate
from app.domains.post.schemas import PostUpdate as ApiPostUpdate
from app.domains.user.service import UserService


@injectable
@dataclass
class PostService:
    repository: PostRepository = inject.me()
    user_service: UserService = inject.me()

    async def create_post(self, post_data: ApiPostCreate) -> PostRead:
        user = await self.user_service.get_user(post_data.user_id)
        if not user:
            raise ValueError(f"User with id {post_data.user_id} not found")

        repo_post = PostCreate(
            title=post_data.title,
            content=post_data.content,
            user_id=post_data.user_id,
        )
        return await self.repository.create(repo_post)

    async def get_post_by_id(self, post_id: str) -> PostRead | None:
        return await self.repository.get_by_id(post_id)

    async def get_posts_by_user(self, user_id: str) -> list[PostRead]:
        return await self.repository.get_all(self.repository.user_id_filter(user_id))

    async def update_post(self, post_id: str, post_data: ApiPostUpdate) -> PostRead:
        await self.repository.get_by_id_or_raise(post_id)

        update_data = PostUpdate(
            title=post_data.title,
            content=post_data.content,
        )
        return await self.repository.update_by_id(update_data, post_id)

    async def delete_post(self, post_id: str) -> None:
        await self.repository.delete_by_id(post_id)

"""Post domain router."""

from antidote import inject
from fastapi import APIRouter, Depends, Response, status

from app.di import hidden_inject
from app.routes import RouteConfig
from app.utils.schemas import CursorPage, CursorParams

from .schemas import PostCreate, PostRead, PostUpdate
from .service import PostService

router = APIRouter()


@router.post("/posts", status_code=status.HTTP_201_CREATED)
@hidden_inject
async def create_post(
    data: PostCreate,
    post_service: PostService = inject.me(),
) -> PostRead:
    return await post_service.create_post(data)


@router.get("/posts/{post_id}")
@hidden_inject
async def get_post(
    post_id: str,
    post_service: PostService = inject.me(),
) -> PostRead:
    return await post_service.get_post(post_id)


@router.get("/users/{user_id}/posts")
@hidden_inject
async def list_posts_for_user(
    user_id: str,
    params: CursorParams = Depends(),
    post_service: PostService = inject.me(),
) -> CursorPage[PostRead]:
    return await post_service.list_posts_for_user(user_id, params)


@router.patch("/posts/{post_id}")
@hidden_inject
async def update_post(
    post_id: str,
    data: PostUpdate,
    post_service: PostService = inject.me(),
) -> PostRead:
    return await post_service.update_post(post_id, data)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@hidden_inject
async def delete_post(
    post_id: str,
    post_service: PostService = inject.me(),
) -> Response:
    await post_service.delete_post(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


route_config = RouteConfig(router=router, prefix="", tags=["posts"])

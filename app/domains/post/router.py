from antidote import inject
from fastapi import APIRouter, HTTPException, status

from app.di import hidden_inject
from app.domains.post.schemas import PostCreate, PostResponse, PostUpdate
from app.domains.post.service import PostService

router = APIRouter(prefix="/post", tags=["post"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
@hidden_inject
async def create_post(
    post_data: PostCreate,
    service: PostService = inject.me(),
) -> PostResponse:
    try:
        post = await service.create_post(post_data)
        return PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            user_id=post.user_id,
            created_at=post.created_at.isoformat(),
            updated_at=post.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{post_id}", response_model=PostResponse)
@hidden_inject
async def get_post(
    post_id: str,
    service: PostService = inject.me(),
) -> PostResponse:
    post = await service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        user_id=post.user_id,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.get("/user/{user_id}", response_model=list[PostResponse])
@hidden_inject
async def get_posts_by_user(
    user_id: str,
    service: PostService = inject.me(),
) -> list[PostResponse]:
    posts = await service.get_posts_by_user(user_id)
    return [
        PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            user_id=post.user_id,
            created_at=post.created_at.isoformat(),
            updated_at=post.updated_at.isoformat(),
        )
        for post in posts
    ]


@router.patch("/{post_id}", response_model=PostResponse)
@hidden_inject
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    service: PostService = inject.me(),
) -> PostResponse:
    try:
        post = await service.update_post(post_id, post_data)
        return PostResponse(
            id=post.id,
            title=post.title,
            content=post.content,
            user_id=post.user_id,
            created_at=post.created_at.isoformat(),
            updated_at=post.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@hidden_inject
async def delete_post(
    post_id: str,
    service: PostService = inject.me(),
) -> None:
    await service.delete_post(post_id)

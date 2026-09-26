"""User domain router."""

from antidote import inject
from fastapi import APIRouter, Depends, Response, status

from app.di import hidden_inject
from app.routes import RouteConfig
from app.utils.schemas import CursorPage, CursorParams

from .schemas import UserCreate, UserRead, UserUpdate
from .service import UserService

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
@hidden_inject
async def create_user(
    data: UserCreate,
    user_service: UserService = inject.me(),
) -> UserRead:
    return await user_service.create_user(data)


@router.get("")
@hidden_inject
async def list_users(
    params: CursorParams = Depends(),
    user_service: UserService = inject.me(),
) -> CursorPage[UserRead]:
    return await user_service.list_users(params)


@router.get("/{user_id}")
@hidden_inject
async def get_user(
    user_id: str,
    user_service: UserService = inject.me(),
) -> UserRead:
    return await user_service.get_user(user_id)


@router.patch("/{user_id}")
@hidden_inject
async def update_user(
    user_id: str,
    data: UserUpdate,
    user_service: UserService = inject.me(),
) -> UserRead:
    return await user_service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@hidden_inject
async def delete_user(
    user_id: str,
    user_service: UserService = inject.me(),
) -> Response:
    await user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


route_config = RouteConfig(router=router, prefix="/users", tags=["users"])

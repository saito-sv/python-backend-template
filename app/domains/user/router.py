"""User API routes."""

from antidote import inject
from fastapi import APIRouter, HTTPException, status

from app.di import hidden_inject
from app.domains.user.schemas import UserCreate, UserRead, UserUpdate
from app.domains.user.service import UserService

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@hidden_inject
async def create_user(
    user_data: UserCreate,
    service: UserService = inject.me(),
) -> UserRead:
    """Create a new user."""
    try:
        return await service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{user_id}", response_model=UserRead)
@hidden_inject
async def get_user(
    user_id: str,
    service: UserService = inject.me(),
) -> UserRead:
    """Get a user by ID."""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", response_model=list[UserRead])
@hidden_inject
async def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = inject.me(),
) -> list[UserRead]:
    """List all users with pagination."""
    return await service.get_users(skip=skip, limit=limit)


@router.patch("/{user_id}", response_model=UserRead)
@hidden_inject
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    service: UserService = inject.me(),
) -> UserRead:
    """Update a user."""
    user = await service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@hidden_inject
async def delete_user(
    user_id: str,
    service: UserService = inject.me(),
) -> None:
    """Delete a user."""
    success = await service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

"""User domain service."""

import bcrypt
from antidote import inject, injectable

from app.exc import EntityExistsException
from app.utils.schemas import CursorPage, CursorParams

from .models import UserDBCreate, UserDBUpdate
from .repository import UserRepository
from .schemas import UserCreate, UserRead, UserUpdate


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


@injectable
class UserService:
    @inject
    def __init__(self, user_repo: UserRepository = inject.me()) -> None:
        self._user_repo = user_repo

    async def create_user(self, data: UserCreate) -> UserRead:
        existing = await self._user_repo.get_one(UserRepository.email_filter(data.email))
        if existing is not None:
            raise EntityExistsException(f"User with email {data.email} already exists")
        return await self._user_repo.create(
            UserDBCreate(
                email=data.email,
                full_name=data.full_name,
                hashed_password=hash_password(data.password),
            )
        )

    async def get_user(self, user_id: str) -> UserRead:
        return await self._user_repo.get_by_id_or_raise(user_id)

    async def get_user_by_email(self, email: str) -> UserRead | None:
        return await self._user_repo.get_one(UserRepository.email_filter(email))

    async def list_users(self, params: CursorParams) -> CursorPage[UserRead]:
        return await self._user_repo.paginate(
            cursor=params.cursor, limit=params.limit, order=params.order
        )

    async def list_inactive_users(self) -> list[UserRead]:
        return await self._user_repo.get_all(UserRepository.is_active_filter(False))

    async def update_user(self, user_id: str, data: UserUpdate) -> UserRead:
        values = data.model_dump(exclude_unset=True)
        password = values.pop("password", None)
        if password is not None:
            values["hashed_password"] = hash_password(password)
        return await self._user_repo.update_by_id(UserDBUpdate(**values), user_id)

    async def delete_user(self, user_id: str) -> None:
        """Soft delete."""
        await self._user_repo.delete_by_id(user_id)

    async def authenticate(self, email: str, password: str) -> UserRead | None:
        result = await self._user_repo.get_with_password_hash(email)
        if result is None:
            return None
        user, hashed_password = result
        if not user.is_active or not verify_password(password, hashed_password):
            return None
        return user

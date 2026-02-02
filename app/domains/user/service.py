"""User service with business logic."""

from dataclasses import dataclass

from antidote import inject, injectable
from passlib.context import CryptContext

from app.domains.user.models import UserCreate, UserRead, UserUpdate
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserCreate as ApiUserCreate
from app.domains.user.schemas import UserUpdate as ApiUserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@injectable
@dataclass
class UserService:
    """Service for user business logic with dependency injection."""

    repository: UserRepository = inject.me()

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_data: ApiUserCreate) -> UserRead:
        """Create a new user."""
        existing_user = await self.repository.get_one(self.repository.email_filter(user_data.email))
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")

        repo_user = UserCreate(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=self._hash_password(user_data.password),
        )
        return await self.repository.create(repo_user)

    async def get_user(self, user_id: str) -> UserRead | None:
        """Get user by ID."""
        return await self.repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> UserRead | None:
        """Get user by email."""
        return await self.repository.get_one(self.repository.email_filter(email))

    async def get_users(self, skip: int = 0, limit: int = 100) -> list[UserRead]:
        """Get all users with pagination."""
        return await self.repository.get_all(limit=limit, offset=skip)

    async def update_user(self, user_id: str, user_data: ApiUserUpdate) -> UserRead | None:
        """Update a user."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None

        update_data = UserUpdate(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=self._hash_password(user_data.password) if user_data.password else None,
            is_active=user_data.is_active,
        )
        return await self.repository.update_by_id(update_data, user_id)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            return False

        await self.repository.delete_by_id(user_id)
        return True

    async def authenticate(self, email: str, password: str) -> UserRead | None:
        """Authenticate a user."""
        user = await self.repository.get_one(self.repository.email_filter(email))
        if not user:
            return None
        if not self._verify_password(password, user.hashed_password):
            return None
        return user

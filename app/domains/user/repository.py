"""User repository."""

from dataclasses import dataclass
from typing import Any

from antidote import injectable

from app.repository.base import MainObjectIdRepository
from app.repository.filter import DataFilter
from app.repository.search import ILikeSearchFilter

from .models import User, UserDBCreate, UserDBUpdate
from .schemas import UserRead


@dataclass
class _EmailFilter(DataFilter[User]):
    email: str

    @property
    def expression(self) -> Any:
        return User.email == self.email


@dataclass
class _IsActiveFilter(DataFilter[User]):
    is_active: bool

    @property
    def expression(self) -> Any:
        return User.is_active == self.is_active


@dataclass
class _EmailSearchFilter(ILikeSearchFilter[User]):
    model_cls = User
    column = "email"


@dataclass
class _FullNameSearchFilter(ILikeSearchFilter[User]):
    model_cls = User
    column = "full_name"


@injectable(lifetime="transient")
class UserRepository(MainObjectIdRepository[UserDBCreate, UserRead, UserDBUpdate, User]):
    _db_class = User
    _read_class = UserRead

    @staticmethod
    def email_filter(email: str) -> DataFilter[User]:
        return _EmailFilter(email)

    @staticmethod
    def is_active_filter(is_active: bool = True) -> DataFilter[User]:
        return _IsActiveFilter(is_active)

    @staticmethod
    def email_search_filter(query: str) -> DataFilter[User]:
        return _EmailSearchFilter(query)

    @staticmethod
    def full_name_search_filter(query: str) -> DataFilter[User]:
        return _FullNameSearchFilter(query)

    async def get_with_password_hash(self, email: str) -> tuple[UserRead, str] | None:
        """For authentication only: ``UserRead`` deliberately never exposes the hash."""
        row = await self._get_one_row(self.email_filter(email), self.active_filter())
        if row is None:
            return None
        return self._create_read_obj(row), row.hashed_password

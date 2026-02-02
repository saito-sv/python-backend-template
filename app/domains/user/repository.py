"""User repository for data access."""

from dataclasses import dataclass
from typing import Any, override

from antidote import injectable

from app.domains.user.models import User, UserCreate, UserRead, UserUpdate
from app.repository.base import MainObjectIdRepository
from app.repository.filter import DataFilter
from app.repository.search import ILikeSearchFilter


@dataclass
class _EmailFilter(DataFilter[User]):
    """Filter users by exact email match."""

    email: str

    @property
    @override
    def expression(self) -> Any:
        return User.email == self.email


@dataclass
class _IsActiveFilter(DataFilter[User]):
    """Filter users by active status."""

    is_active: bool

    @property
    @override
    def expression(self) -> Any:
        return User.is_active == self.is_active


class _UserILikeSearchFilter(ILikeSearchFilter[User]):
    """Base class for User ILIKE search filters."""

    model_cls = User


@dataclass
class _EmailSearchFilter(_UserILikeSearchFilter):
    """Search users by email (case-insensitive partial match)."""

    column = "email"


@dataclass
class _FullNameSearchFilter(_UserILikeSearchFilter):
    """Search users by full name (case-insensitive partial match)."""

    column = "full_name"


@injectable(lifetime="transient")
class UserRepository(MainObjectIdRepository[UserCreate, UserRead, UserUpdate, User]):
    """Repository for user data access with filter support.

    This repository demonstrates the filter pattern with:
    - Exact match filters (e.g., email_filter)
    - Boolean filters (e.g., is_active_filter)
    - Search filters using ILIKE for partial matching (e.g., email_search_filter)

    Example usage:
        # Exact match
        user = await repo.get_one(repo.email_filter("john@example.com"))

        # Boolean filter
        active_users = await repo.get_many(repo.is_active_filter(True))

        # Search filter (partial match)
        users = await repo.get_many(repo.email_search_filter("john"))

        # Combine multiple filters
        users = await repo.get_many(
            repo.is_active_filter(True),
            repo.email_search_filter("example.com")
        )
    """

    _db_class = User
    _read_class = UserRead

    @staticmethod
    def email_filter(email: str) -> _EmailFilter:
        """Create a filter for exact email match."""
        return _EmailFilter(email)

    @staticmethod
    def is_active_filter(is_active: bool = True) -> _IsActiveFilter:
        """Create a filter for active status."""
        return _IsActiveFilter(is_active)

    @staticmethod
    def email_search_filter(query: str) -> _EmailSearchFilter:
        """Create a search filter for email (case-insensitive partial match)."""
        return _EmailSearchFilter(query)

    @staticmethod
    def full_name_search_filter(query: str) -> _FullNameSearchFilter:
        """Create a search filter for full name (case-insensitive partial match)."""
        return _FullNameSearchFilter(query)

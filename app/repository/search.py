"""Search filter utilities for text-based queries."""

from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar, override

from sqlalchemy import Column
from sqlmodel import SQLModel

from app.repository.filter import DataFilter

T = TypeVar("T", bound=SQLModel)


@dataclass
class ILikeSearchFilter[T: SQLModel](DataFilter[T]):
    """Base class for case-insensitive LIKE search filters.

    This filter performs a case-insensitive partial match search on a specific column.
    Subclasses should define the model_cls and column as class variables.

    Example:
        @dataclass
        class _EmailSearchFilter(ILikeSearchFilter[User]):
            model_cls = User
            column = "email"

        # Usage
        filter = _EmailSearchFilter("john@example.com")
        users = await repo.get_many(filter)
    """

    query: str
    model_cls: ClassVar[type[SQLModel]]
    column: ClassVar[str]

    @property
    def _column(self) -> Column:
        """Get the column object from the model."""
        return getattr(self.model_cls, self.column)

    @property
    @override
    def expression(self) -> Any:
        """Generate ILIKE expression for partial matching."""
        return self._column.ilike(f"%{self.query}%")

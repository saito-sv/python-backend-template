from dataclasses import dataclass
from typing import Any, ClassVar, override

from sqlalchemy import Column
from sqlmodel import SQLModel

from app.repository.filter import DataFilter


@dataclass
class ILikeSearchFilter[T: SQLModel](DataFilter[T]):
    """Case-insensitive partial match on one column.

    Example:
        @dataclass
        class _EmailSearchFilter(ILikeSearchFilter[User]):
            model_cls = User
            column = "email"
    """

    query: str
    model_cls: ClassVar[type[SQLModel]]
    column: ClassVar[str]

    @property
    def _column(self) -> Column:
        return getattr(self.model_cls, self.column)

    @property
    @override
    def expression(self) -> Any:
        return self._column.ilike(f"%{self.query}%")

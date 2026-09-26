"""Composable query filters for repositories."""

import abc
from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql import Delete as SQLAlchemyDelete
from sqlalchemy.sql import Update as SQLAlchemyUpdate
from sqlmodel import SQLModel, and_, not_, or_
from sqlmodel.sql.expression import SelectOfScalar


class DataFilter[D: SQLModel](abc.ABC):
    def filter(self, statement: SelectOfScalar[D]) -> SelectOfScalar[D]:
        return statement.where(self.expression)

    @property
    @abc.abstractmethod
    def expression(self) -> Any:
        """SQLAlchemy expression, e.g. ``User.email == self.email``."""
        ...

    def filter_update(self, statement: SQLAlchemyUpdate) -> SQLAlchemyUpdate:
        return self.filter(statement)  # type: ignore[arg-type,return-value]

    def filter_delete(self, statement: SQLAlchemyDelete) -> SQLAlchemyDelete:
        return self.filter(statement)  # type: ignore[arg-type,return-value]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"


@dataclass
class IDFilter[D: SQLModel](DataFilter[D]):
    model_cls: type[D]
    id: str

    @property
    def expression(self) -> Any:
        return self.model_cls.id == self.id  # type: ignore[attr-defined]


@dataclass
class MultiIDFilter[D: SQLModel](DataFilter[D]):
    model_cls: type[D]
    ids: list[str] | set[str]

    @property
    def expression(self) -> Any:
        return self.model_cls.id.in_(self.ids)  # type: ignore[attr-defined]


@dataclass
class ActiveFilter[D: SQLModel](DataFilter[D]):
    """Excludes soft-deleted rows."""

    model_cls: type[D]

    @property
    def expression(self) -> Any:
        return self.model_cls.deleted_at.is_(None)  # type: ignore[attr-defined]


@dataclass
class AndFilter[D: SQLModel](DataFilter[D]):
    filters: list[DataFilter[D]]

    @property
    def expression(self) -> Any:
        return and_(*[f.expression for f in self.filters])


@dataclass
class OrFilter[D: SQLModel](DataFilter[D]):
    filters: list[DataFilter[D]]

    @property
    def expression(self) -> Any:
        return or_(*[f.expression for f in self.filters])


@dataclass
class NotFilter[D: SQLModel](DataFilter[D]):
    inner: DataFilter[D]

    @property
    def expression(self) -> Any:
        return not_(self.inner.expression)


def and_filter[D: SQLModel](*filters: DataFilter[D] | None) -> DataFilter[D]:
    active = [f for f in filters if f is not None]
    return active[0] if len(active) == 1 else AndFilter(filters=active)


def or_filter[D: SQLModel](*filters: DataFilter[D] | None) -> DataFilter[D]:
    active = [f for f in filters if f is not None]
    return active[0] if len(active) == 1 else OrFilter(filters=active)


def not_filter[D: SQLModel](f: DataFilter[D]) -> DataFilter[D]:
    return NotFilter(inner=f)

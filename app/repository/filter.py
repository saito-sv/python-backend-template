"""Data filter classes for repository queries."""

import abc
from typing import Any

from sqlalchemy.sql import Delete as SQLAlchemyDelete
from sqlalchemy.sql import Update as SQLAlchemyUpdate
from sqlmodel import SQLModel
from sqlmodel.sql.expression import SelectOfScalar


class DataFilter[D: SQLModel](abc.ABC):
    def filter(self, statement: SelectOfScalar[D]) -> SelectOfScalar[D]:
        return statement.where(self.expression)

    @property
    @abc.abstractmethod
    def expression(self) -> Any:
        """
        The expression for this filter, such as self._db_class.id == self.id
        """
        ...

    def filter_update(self, statement: SQLAlchemyUpdate) -> SQLAlchemyUpdate:
        return self.filter(statement)  # type: ignore[return-value]

    def filter_delete(self, statement: SQLAlchemyDelete) -> SQLAlchemyDelete:
        return self.filter(statement)  # type: ignore[return-value]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"

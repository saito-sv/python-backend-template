"""Base repository classes for data access patterns."""

import abc
from collections.abc import Sequence
from typing import Any, cast

from antidote import inject
from sqlalchemy import desc, func, not_
from sqlmodel import SQLModel, and_, delete, insert, or_, select, update
from sqlmodel.sql.expression import SelectOfScalar

from app.database.engine import AsyncSessionFactory, async_session_factory
from app.database.session import SessionManager
from app.exc import EntityNotFoundException
from app.repository.filter import DataFilter


class BaseRepository[
    Create: SQLModel,
    Read: SQLModel,
    Update: SQLModel,
    DB: SQLModel,
](SessionManager, abc.ABC):
    """Base repository with common CRUD operations and filter support."""

    _db_class: type[DB]
    _read_class: type[Read]

    @inject
    def __init__(
        self,
        session_factory: AsyncSessionFactory = inject[async_session_factory],
    ):
        self.session_factory = session_factory

    def _default_select_statement(self) -> SelectOfScalar[DB]:
        """Get the default select statement."""
        return select(self._db_class)

    async def create(self, obj_in: Create) -> Read:
        """Create a new object."""
        db_obj = self._create_db_obj(obj_in)
        async with self._managed_session() as session:
            session.add(db_obj)
        return self._create_read_obj(db_obj)

    async def get_one(
        self,
        *filters: DataFilter[DB] | None,
    ) -> Read | None:
        """Get one object matching the filters."""
        db_obj = await self._get_one_row(*filters)
        if db_obj is None:
            return None
        return self._create_read_obj(db_obj)

    async def _get_one_row(
        self,
        *filters: DataFilter[DB] | None,
    ) -> DB | None:
        """Get one database row matching the filters."""
        statement = self._default_select_statement()
        for filter in self._all_filters(*filters):
            statement = filter.filter(statement)
        async with self._managed_session(auto_commit=False) as session:
            query = await session.execute(statement)
            db_obj = query.scalar_one_or_none()
        return db_obj

    async def get_all(
        self,
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[Read]:
        """Get all objects matching the filters with pagination support."""
        statement = self._default_select_statement()
        db_objs = await self._filter_and_execute_list_statement(
            statement,
            *filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
        return self._create_read_objs(db_objs)

    async def _filter_and_execute_list_statement(
        self,
        statement: SelectOfScalar[DB],
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> Sequence[DB]:
        """Apply filters and execute a list query."""
        for filter in self._all_filters(*filters):
            statement = filter.filter(statement)
        if order_by is not None:
            order_col = getattr(self._db_class, order_by)
            statement = statement.order_by(desc(order_col) if order_desc else order_col)
        if limit is not None:
            statement = statement.limit(limit)
        if offset is not None:
            statement = statement.offset(offset)
        async with self._managed_session(auto_commit=False) as session:
            result = await session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        *filters: DataFilter[DB] | None,
    ) -> int:
        """Count objects matching the filters."""
        statement = select(func.count()).select_from(self._db_class)
        for filter in self._all_filters(*filters):
            statement = filter.filter(statement)  # type: ignore[assignment]
        async with self._managed_session(auto_commit=False) as session:
            result = await session.execute(statement)
        return cast(int, result.scalar_one())

    async def update(
        self,
        obj_in: Update,
        *filters: DataFilter[DB] | None,
    ) -> list[Read]:
        """Update objects matching the filters."""
        statement = update(self._db_class)
        for filter in self._all_filters(*filters):
            statement = filter.filter_update(statement)
        statement = statement.values(**obj_in.model_dump(exclude_unset=True))
        async with self._managed_session() as session:
            await session.execute(statement)  # type: ignore[arg-type]
        return await self.get_all(*filters)

    async def delete(
        self,
        *filters: DataFilter[DB] | None,
    ) -> int:
        """Delete objects matching the filters and return count."""
        statement = delete(self._db_class)
        for filter in self._all_filters(*filters):
            statement = filter.filter_delete(statement)
        async with self._managed_session() as session:
            query = await session.execute(statement)  # type: ignore[arg-type]
        return query.rowcount

    def _create_dict(self, obj_in: Create) -> dict[str, Any]:
        """Convert create schema to dict."""
        return obj_in.model_dump()

    def _create_db_obj(self, obj_in: Create) -> DB:
        """Create database object from create schema."""
        return self._db_class(**self._create_dict(obj_in))

    def _create_read_obj(self, db_obj: DB) -> Read:
        """Create read schema from database object."""
        return self._read_class.model_validate(db_obj)

    def _create_read_objs(self, db_objs: Sequence[DB]) -> list[Read]:
        """Create read schemas from database objects."""
        return [self._create_read_obj(db_obj) for db_obj in db_objs]

    @classmethod
    def _all_filters(
        cls,
        *filters: DataFilter[DB] | None,
    ) -> list[DataFilter[DB]]:
        """Get all defined filters."""
        return [filter for filter in filters if filter is not None]


class MainObjectIdRepository[
    Create: SQLModel,
    Read: SQLModel,
    Update: SQLModel,
    DB: SQLModel,
](BaseRepository[Create, Read, Update, DB]):
    """Main repository for models with string ID primary keys."""

    async def get_by_id(self, id: str) -> Read | None:
        """Get object by ID."""
        return await self.get_one(self.id_filter(id))

    async def get_by_id_or_raise(self, id: str) -> Read:
        """Get object by ID or raise EntityNotFoundException if not found."""
        db_obj = await self.get_by_id(id)
        if db_obj is None:
            raise EntityNotFoundException(self._db_class, id=id)
        return db_obj

    async def get_one_or_raise(self, *filters: DataFilter[DB] | None) -> Read:
        """Get one object matching the filters or raise EntityNotFoundException if not found."""
        db_obj = await self.get_one(*filters)
        if db_obj is None:
            raise EntityNotFoundException(self._db_class, filters=filters)
        return db_obj

    async def get_first(
        self,
        *filters: DataFilter[DB] | None,
        order_by: str,
        order_desc: bool = False,
    ) -> Read | None:
        """Get the first object matching the filters, ordered by the specified field."""
        objects = await self.get_all(
            *filters,
            order_by=order_by,
            order_desc=order_desc,
            limit=1,
        )
        return objects[0] if objects else None

    async def get_first_or_raise(
        self,
        *filters: DataFilter[DB] | None,
        order_by: str,
        order_desc: bool = False,
    ) -> Read:
        """Get the first object matching the filters or raise EntityNotFoundException if not found."""
        obj = await self.get_first(*filters, order_by=order_by, order_desc=order_desc)
        if obj is None:
            raise EntityNotFoundException(self._db_class, filters=filters)
        return obj

    async def list_ids(
        self,
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[str]:
        """Get list of IDs matching the filters."""
        statement = select(self._db_class.id)  # type: ignore[attr-defined]
        db_ids = await self._filter_and_execute_list_statement(
            statement,
            *filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
        return [str(id) for id in db_ids]

    async def create_many(self, objs_in: Sequence[Create]) -> list[str]:
        """Create multiple objects and return their IDs."""
        if not objs_in:
            return []
        statement = (
            insert(self._db_class)
            .values([self._create_dict(obj) for obj in objs_in])
            .returning(self._db_class.id)  # type: ignore[attr-defined]
        )
        async with self._managed_session() as session:
            result = await session.execute(statement)
        return [str(row[0]) for row in result.all()]

    async def update_by_id(self, obj_in: Update, id: str) -> Read:
        """Update object by ID."""
        results = await self.update(obj_in, self.id_filter(id))
        if not results:
            raise EntityNotFoundException(self._db_class, id=id)
        return results[0]

    async def delete_by_id(self, id: str) -> None:
        """Delete object by ID."""
        num_deleted = await self.delete(self.id_filter(id))
        if num_deleted == 0:
            raise EntityNotFoundException(self._db_class, id=id)

    @classmethod
    def id_filter(cls, id: str) -> DataFilter[DB]:
        """Create a filter for ID."""
        db_class = cls._db_class

        class _IDFilter(DataFilter[DB]):
            def __init__(self, id: str):
                self.id = id

            @property
            def expression(self) -> Any:
                return db_class.id == self.id  # type: ignore[attr-defined]

        return _IDFilter(id)

    @classmethod
    def multi_id_filter(cls, ids: Sequence[str] | set[str]) -> DataFilter[DB]:
        """Create a filter for multiple IDs."""
        db_class = cls._db_class

        class _MultiIDFilter(DataFilter[DB]):
            def __init__(self, ids: Sequence[str] | set[str]):
                self.ids = ids

            @property
            def expression(self) -> Any:
                return db_class.id.in_(self.ids)  # type: ignore[attr-defined]

        return _MultiIDFilter(ids)

    @classmethod
    def or_filter(cls, *filters: DataFilter[DB] | None) -> DataFilter[DB]:
        """Combine filters with OR logic."""
        _filters = [filter for filter in filters if filter is not None]
        if len(_filters) == 1:
            return _filters[0]

        class _OrFilter(DataFilter[DB]):
            def __init__(self, *filters: DataFilter[DB]):
                self.filters = filters

            @property
            def expression(self) -> Any:
                return or_(*[filter.expression for filter in self.filters])

        return _OrFilter(*_filters)

    @classmethod
    def and_filter(cls, *filters: DataFilter[DB] | None) -> DataFilter[DB]:
        """Combine filters with AND logic."""

        class _AndFilter(DataFilter[DB]):
            def __init__(self, *filters: DataFilter[DB] | None):
                self.filters = [filter for filter in filters if filter is not None]

            @property
            def expression(self) -> Any:
                return and_(*[filter.expression for filter in self.filters])

        return _AndFilter(*filters)

    @classmethod
    def not_filter(cls, filter: DataFilter[DB]) -> DataFilter[DB]:
        """Negate a filter with NOT logic."""

        class _NotFilter(DataFilter[DB]):
            def __init__(self, filter: DataFilter[DB]):
                self._filter = filter

            @property
            def expression(self) -> Any:
                return not_(self._filter.expression)

        return _NotFilter(filter)

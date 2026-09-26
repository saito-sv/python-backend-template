"""Base repositories with CRUD, filters, pagination and soft delete."""

import abc
from collections.abc import Sequence
from typing import Literal, cast

from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlmodel import SQLModel, delete, insert, select, update
from sqlmodel.sql.expression import SelectOfScalar

from app.database.engine import AsyncSessionFactory, async_session_factory
from app.database.model_base import utcnow
from app.database.session import SessionManager
from app.exc import EntityNotFoundException
from app.repository.filter import ActiveFilter, DataFilter, IDFilter, MultiIDFilter
from app.utils.schemas import CursorPage


class BaseRepository[
    Create: BaseModel,
    Read: BaseModel,
    Update: BaseModel,
    DB: SQLModel,
](SessionManager, abc.ABC):
    _db_class: type[DB]
    _read_class: type[Read]

    def __init__(self, session_factory: AsyncSessionFactory = async_session_factory):
        super().__init__(session_factory)

    def _default_select_statement(self) -> SelectOfScalar[DB]:
        return select(self._db_class)

    async def create(self, obj_in: Create) -> Read:
        db_obj = self._create_db_obj(obj_in)
        async with self.session() as s:
            s.add(db_obj)
        return self._create_read_obj(db_obj)

    async def get_one(self, *filters: DataFilter[DB] | None) -> Read | None:
        db_obj = await self._get_one_row(*filters)
        return None if db_obj is None else self._create_read_obj(db_obj)

    async def _get_one_row(self, *filters: DataFilter[DB] | None) -> DB | None:
        statement = self._default_select_statement()
        for f in self._all_filters(*filters):
            statement = f.filter(statement)
        async with self.session(auto_commit=False) as s:
            return (await s.exec(statement)).one_or_none()

    async def get_all(
        self,
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> list[Read]:
        db_objs = await self._filter_and_execute_list_statement(
            self._default_select_statement(),
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
        for f in self._all_filters(*filters):
            statement = f.filter(statement)
        if order_by is not None:
            order_col = getattr(self._db_class, order_by)
            statement = statement.order_by(desc(order_col) if order_desc else order_col)
        if limit is not None:
            statement = statement.limit(limit)
        if offset is not None:
            statement = statement.offset(offset)
        async with self.session(auto_commit=False) as s:
            return (await s.exec(statement)).all()

    async def count(self, *filters: DataFilter[DB] | None) -> int:
        statement = select(func.count()).select_from(self._db_class)
        for f in self._all_filters(*filters):
            statement = f.filter(statement)  # type: ignore[arg-type,assignment]
        async with self.session(auto_commit=False) as s:
            return cast(int, (await s.exec(statement)).one())

    async def update(self, obj_in: Update, *filters: DataFilter[DB] | None) -> list[Read]:
        values = obj_in.model_dump(exclude_unset=True)
        if not values:
            return await self.get_all(*filters)
        if hasattr(self._db_class, "updated_at"):
            values.setdefault("updated_at", utcnow())
        statement = update(self._db_class)
        for f in self._all_filters(*filters):
            statement = f.filter_update(statement)
        async with self.session() as s:
            await s.exec(statement.values(**values))  # type: ignore[arg-type]
        return await self.get_all(*filters)

    async def delete(self, *filters: DataFilter[DB] | None) -> int:
        """Hard delete; returns the number of rows removed."""
        statement = delete(self._db_class)
        for f in self._all_filters(*filters):
            statement = f.filter_delete(statement)  # type: ignore[arg-type]
        async with self.session() as s:
            result = await s.exec(statement)  # type: ignore[arg-type]
            return result.rowcount or 0

    def _create_db_obj(self, obj_in: Create) -> DB:
        return self._db_class(**obj_in.model_dump())

    def _create_read_obj(self, db_obj: DB) -> Read:
        return self._read_class.model_validate(db_obj)

    def _create_read_objs(self, db_objs: Sequence[DB]) -> list[Read]:
        return [self._create_read_obj(db_obj) for db_obj in db_objs]

    @classmethod
    def _all_filters(cls, *filters: DataFilter[DB] | None) -> list[DataFilter[DB]]:
        return [f for f in filters if f is not None]


class BaseManyToManyRepository[DB: SQLModel](SessionManager):
    """For join tables with composite primary keys."""

    _db_class: type[DB]

    def __init__(self, session_factory: AsyncSessionFactory = async_session_factory):
        super().__init__(session_factory)

    async def create(self, obj: DB) -> None:
        async with self.session() as s:
            s.add(obj)

    async def delete(self, pk: tuple[str, str]) -> bool:
        async with self.session() as s:
            row = await s.get(self._db_class, pk)
            if row is None:
                return False
            await s.delete(row)
            return True


class MainObjectIdRepository[
    Create: BaseModel,
    Read: BaseModel,
    Update: BaseModel,
    DB: SQLModel,
](BaseRepository[Create, Read, Update, DB]):
    """For tables with a string ``id`` and ``deleted_at``.

    Soft-deleted rows are excluded unless ``include_deleted=True``.
    """

    def active_filter(self) -> DataFilter[DB]:
        return ActiveFilter(model_cls=self._db_class)

    def id_filter(self, id: str) -> DataFilter[DB]:
        return IDFilter(model_cls=self._db_class, id=id)

    def multi_id_filter(self, ids: list[str] | set[str]) -> DataFilter[DB]:
        return MultiIDFilter(model_cls=self._db_class, ids=list(ids))

    def _with_active(
        self, filters: tuple[DataFilter[DB] | None, ...], include_deleted: bool
    ) -> tuple[DataFilter[DB] | None, ...]:
        return filters if include_deleted else (*filters, self.active_filter())

    async def get_one(
        self, *filters: DataFilter[DB] | None, include_deleted: bool = False
    ) -> Read | None:
        return await super().get_one(*self._with_active(filters, include_deleted))

    async def get_all(
        self,
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
        include_deleted: bool = False,
    ) -> list[Read]:
        return await super().get_all(
            *self._with_active(filters, include_deleted),
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )

    async def update(
        self,
        obj_in: Update,
        *filters: DataFilter[DB] | None,
        include_deleted: bool = False,
    ) -> list[Read]:
        return await super().update(obj_in, *self._with_active(filters, include_deleted))

    async def get_by_id(self, id: str, include_deleted: bool = False) -> Read | None:
        return await self.get_one(self.id_filter(id), include_deleted=include_deleted)

    async def get_by_id_or_raise(self, id: str, include_deleted: bool = False) -> Read:
        db_obj = await self.get_by_id(id, include_deleted=include_deleted)
        if db_obj is None:
            raise EntityNotFoundException(self._db_class, id=id)
        return db_obj

    async def get_one_or_raise(
        self, *filters: DataFilter[DB] | None, include_deleted: bool = False
    ) -> Read:
        db_obj = await self.get_one(*filters, include_deleted=include_deleted)
        if db_obj is None:
            raise EntityNotFoundException(self._db_class, filters=list(filters))
        return db_obj

    async def get_first(
        self,
        *filters: DataFilter[DB] | None,
        order_by: str,
        order_desc: bool = False,
        include_deleted: bool = False,
    ) -> Read | None:
        objects = await self.get_all(
            *filters,
            order_by=order_by,
            order_desc=order_desc,
            limit=1,
            include_deleted=include_deleted,
        )
        return objects[0] if objects else None

    async def get_first_or_raise(
        self,
        *filters: DataFilter[DB] | None,
        order_by: str,
        order_desc: bool = False,
        include_deleted: bool = False,
    ) -> Read:
        obj = await self.get_first(
            *filters, order_by=order_by, order_desc=order_desc, include_deleted=include_deleted
        )
        if obj is None:
            raise EntityNotFoundException(self._db_class, filters=list(filters))
        return obj

    async def list_ids(
        self,
        *filters: DataFilter[DB] | None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
        include_deleted: bool = False,
    ) -> list[str]:
        statement = select(self._db_class.id)  # type: ignore[attr-defined]
        db_ids = await self._filter_and_execute_list_statement(
            statement,
            *self._with_active(filters, include_deleted),
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
        return [str(id) for id in db_ids]

    async def create_many(self, objs_in: Sequence[Create]) -> list[str]:
        if not objs_in:
            return []
        # Build DB objects first so the id and timestamp default factories run.
        rows = [self._create_db_obj(obj).model_dump() for obj in objs_in]
        statement = (
            insert(self._db_class).values(rows).returning(self._db_class.id)  # type: ignore[attr-defined]
        )
        async with self.session() as s:
            result = await s.exec(statement)
            return [str(id) for id in result.scalars().all()]

    async def update_by_id(self, obj_in: Update, id: str, include_deleted: bool = False) -> Read:
        results = await self.update(obj_in, self.id_filter(id), include_deleted=include_deleted)
        if not results:
            raise EntityNotFoundException(self._db_class, id=id)
        return results[0]

    async def delete_by_id(self, id: str, hard: bool = False) -> None:
        """Soft delete by default; ``hard=True`` removes the row."""
        if hard:
            if await self.delete(self.id_filter(id)) == 0:
                raise EntityNotFoundException(self._db_class, id=id)
            return

        statement = (
            update(self._db_class)
            .where(self._db_class.id == id)  # type: ignore[attr-defined]
            .where(self._db_class.deleted_at.is_(None))  # type: ignore[attr-defined]
            .values(deleted_at=utcnow())
            .returning(self._db_class.id)  # type: ignore[attr-defined]
        )
        async with self.session() as s:
            result = await s.exec(statement)  # type: ignore[arg-type]
            if not result.all():
                raise EntityNotFoundException(self._db_class, id=id)

    async def paginate(
        self,
        *filters: DataFilter[DB] | None,
        cursor: str | None = None,
        limit: int,
        order: Literal["asc", "desc"] = "desc",
        include_deleted: bool = False,
    ) -> CursorPage[Read]:
        """Keyset pagination on ``id``.

        Ids are prefixed ULIDs, so ordering by id is ordering by creation time and
        ``WHERE id < cursor`` is an index range scan on the primary key, independent of
        how deep the page is. Fetches ``limit + 1`` rows to know whether a next page exists.
        """
        id_col = self._db_class.id  # type: ignore[attr-defined]
        statement = self._default_select_statement()
        for f in self._all_filters(*self._with_active(filters, include_deleted)):
            statement = f.filter(statement)
        if cursor is not None:
            statement = statement.where(id_col < cursor if order == "desc" else id_col > cursor)
        statement = statement.order_by(id_col.desc() if order == "desc" else id_col.asc())
        statement = statement.limit(limit + 1)

        async with self.session(auto_commit=False) as s:
            db_objs = list((await s.exec(statement)).all())

        has_more = len(db_objs) > limit
        items = self._create_read_objs(db_objs[:limit])
        next_cursor = items[-1].id if has_more and items else None  # type: ignore[attr-defined]
        return CursorPage(items=items, next_cursor=next_cursor)

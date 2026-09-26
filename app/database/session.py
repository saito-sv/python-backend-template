from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.engine import AsyncSessionFactory, async_session_factory
from app.exc import DuplicateEntityException, ForeignKeyViolationException


def map_integrity_error(e: Exception) -> Exception:
    """Map Postgres integrity errors to database-agnostic application exceptions."""
    if isinstance(e, IntegrityError) and e.orig is not None and hasattr(e.orig, "pgcode"):
        pgcode = e.orig.pgcode  # pyright: ignore[reportAttributeAccessIssue]
        if pgcode == "23505":
            return DuplicateEntityException(e)
        if pgcode == "23503":
            return ForeignKeyViolationException(e)
    return e


class SessionManager:
    def __init__(self, session_factory: AsyncSessionFactory):
        self.session_factory = session_factory

    @asynccontextmanager
    async def session(self, *, auto_commit: bool = True):
        """Yield a session; commit on success, roll back and map errors on failure."""
        async with self.session_factory() as db_session:
            try:
                yield db_session
                if auto_commit:
                    await db_session.commit()
            except Exception as e:
                await db_session.rollback()
                raise map_integrity_error(e) from e


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency yielding a raw session."""
    async with async_session_factory() as db_session:
        yield db_session

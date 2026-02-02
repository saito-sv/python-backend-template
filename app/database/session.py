from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import AsyncSessionFactory, async_session_factory
from app.repository.exceptions import DuplicateEntityException


class SessionManager:
    """Manages database sessions with automatic commit and error handling."""

    def __init__(self, session_factory: AsyncSessionFactory):
        self.session_factory = session_factory

    @asynccontextmanager
    async def _managed_session(self, *, auto_commit: bool = True):
        """Context manager for session handling with automatic commit."""
        async with self.session_factory() as session:
            try:
                yield session
                if auto_commit:
                    await session.commit()
            except Exception as e:
                raise _maybe_abstract_exception(e) from e


def _maybe_abstract_exception(e: Exception) -> Exception:
    """
    Abstract database-specific exceptions to application exceptions.
    
    This allows swapping database implementations without changing application code.
    """
    if (
        isinstance(e, IntegrityError)
        and e.orig is not None
        and hasattr(e.orig, "pgcode")
        and e.orig.pgcode == "23505"  # pyright: ignore[reportAttributeAccessIssue]
    ):
        return DuplicateEntityException(e)
    return e


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_factory() as session:
        yield session

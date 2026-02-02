from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from settings.config import settings


def create_engine() -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(
        str(settings.database_url),
        echo=settings.database_echo,
        future=True,
        pool_pre_ping=True,
    )


engine = create_engine()


AsyncSessionFactory = Callable[[], AsyncSession]


def create_async_session_factory(eng: AsyncEngine) -> AsyncSessionFactory:
    """Create a session factory for the given engine."""
    def _async_session_factory() -> AsyncSession:
        return AsyncSession(eng, expire_on_commit=False)

    return _async_session_factory


async_session_factory = create_async_session_factory(engine)

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import DatabaseConfig, load
from app.telemetry import instrument_engine

AsyncSessionFactory = Callable[[], AsyncSession]


def make_engine(cfg: DatabaseConfig) -> AsyncEngine:
    return create_async_engine(cfg.url, echo=cfg.echo, future=True, pool_pre_ping=True)


def make_session_factory(eng: AsyncEngine) -> AsyncSessionFactory:
    def _factory() -> AsyncSession:
        return AsyncSession(eng, expire_on_commit=False)

    return _factory


engine = make_engine(load("database").database)
instrument_engine(engine)
async_session_factory = make_session_factory(engine)

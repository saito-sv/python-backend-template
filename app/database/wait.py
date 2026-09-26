"""Wait until Postgres accepts connections (``python -m app.database.wait``)."""

import asyncio

import sqlalchemy.exc
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_db_availability(
    db_url: str, db_name: str = "Database", total_wait_time: int = 120, sleep_time: int = 2
) -> None:
    engine = create_async_engine(db_url)
    try:
        while total_wait_time > 0:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                print(f"{db_name} is ready, continuing app start...")
                return
            except (sqlalchemy.exc.OperationalError, OSError, TimeoutError) as e:
                print(f"Waiting for {db_name} to be available... ({type(e).__name__}: {e})")
                await asyncio.sleep(sleep_time)
                total_wait_time -= sleep_time
    finally:
        await engine.dispose()

    raise ConnectionError(
        f"Timed out while waiting to connect to the {db_name}. "
        "Please inspect the db logs for more information."
    )


if __name__ == "__main__":
    from app.config import load

    asyncio.run(check_db_availability(load("database").database.url))

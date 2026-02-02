"""Script that checks and waits for db to be available."""

import asyncio
import time

import sqlalchemy
import sqlalchemy.exc
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_db_availability(
    db_url: str, db_name: str = "Database", total_wait_time: int = 20, sleep_time: int = 1
) -> None:
    """Check if database is available and wait if not.

    Args:
        db_url: Database connection URL
        db_name: Name of database for logging
        total_wait_time: Maximum time to wait in seconds
        sleep_time: Time to sleep between checks in seconds

    Raises:
        ConnectionError: If database is not available after total_wait_time
    """
    while total_wait_time > 0:
        try:
            engine = create_async_engine(db_url)
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                success = result.fetchall()
            await engine.dispose()
            if success:
                print(f"{db_name} is ready, continuing app start...")
                break
        except (sqlalchemy.exc.OperationalError, ConnectionRefusedError):
            print(f"Waiting for {db_name} to be available...")
            time.sleep(sleep_time)
            total_wait_time -= sleep_time

    if total_wait_time <= 0:
        raise ConnectionError(
            f"Timed out while waiting to connect to the {db_name}. "
            "Please inspect the db logs for more information."
        )


if __name__ == "__main__":
    from settings.config import settings

    asyncio.run(check_db_availability(str(settings.database_url), db_name="Database"))

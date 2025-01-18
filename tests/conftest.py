import os
import sys

import pytest_asyncio
import aiosqlite

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_ROUTE = "weather_test.db"
os.environ["DB_ROUTE"] = DB_ROUTE

from app.db import init_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def reset_test_db():
    """
    Очищаем базу перед выполнением каждого тестового файла.
    """
    async with aiosqlite.connect(DB_ROUTE) as db:
        await db.execute("DROP TABLE IF EXISTS users")
        await db.execute("DROP TABLE IF EXISTS cities")
        await db.execute("DROP TABLE IF EXISTS weather_data")
        
        await db.commit()

    await init_db(DB_ROUTE)

    yield

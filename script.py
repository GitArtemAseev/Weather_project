import sys
import asyncio

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager

from app.routes import users, cities, weather
from app.db import init_db
from app.service import upd_data_to_db
from settings import DB_ROUTE, REFRESH_TIME

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Вызывает upd_data_to_db раз в 15 минут (если REFRESH_TIME=15)
    """
    try:
        scheduler.add_job(
            upd_data_to_db,
            trigger=IntervalTrigger(minutes=REFRESH_TIME),
            id='weather_update_job',
            replace_existing=True
        )
        scheduler.start()
        print("Планировщик обновления данных о погоде запущен.")
        yield
    except Exception as e:
        print(f"Ошибка инициализации планировщика: {e}")
    finally:
        scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/users")
app.include_router(cities.router, prefix="/cities")
app.include_router(weather.router, prefix="/weather")


if __name__ == "__main__":
    import uvicorn
    asyncio.run(init_db(DB_ROUTE))
    uvicorn.run("script:app", host="127.0.0.1", port=8000, reload=True)
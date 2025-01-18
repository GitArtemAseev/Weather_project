import aiosqlite

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from settings import DB_ROUTE


router = APIRouter()

@router.post("/register")
async def register_user(name: str = Query(..., description="Имя пользователя")):
    """
    Регистрирует пользователя по имени или возвращает существующего
    """
    try:
        async with aiosqlite.connect(DB_ROUTE) as db:
            async with db.execute("SELECT id FROM users WHERE name = ?", (name,)) as cursor:
                user = await cursor.fetchone()

            if user:
                user_id = user[0]
                return JSONResponse(status_code=200,content={"message": "Пользователь уже существует", "id": user_id})
            else:
                await db.execute("INSERT INTO users (name) VALUES (?)", (name,))
                await db.commit()

                async with db.execute("SELECT last_insert_rowid()") as cursor:
                    user_id = await cursor.fetchone()
                    user_id = user_id[0] if user_id else None

                return JSONResponse(status_code=201,content={"message": "Пользователь зарегистрирован", "id": user_id})
    
    except aiosqlite.Error as e:
        return JSONResponse(status_code=500,content={"message": f"Ошибка базы данных: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500,content={"message": f"Неизвестная ошибка: {str(e)}"})
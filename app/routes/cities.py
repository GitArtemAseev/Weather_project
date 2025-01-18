from datetime import datetime
from typing import Optional, List

import aiosqlite
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse

from app.models import CityRequest
from app.service import upd_data_to_db
from settings import DB_ROUTE


router = APIRouter()

@router.post('/add_city')
async def add_city(city_request: CityRequest,
                   user_id: Optional[str] = Query(None, description="ID пользователя (необязательно)")):
    """
    Добавляет город в список отслеживания для пользователя (если указан user_id) или общий список.
    """
    try:
        async with aiosqlite.connect(DB_ROUTE) as db:
            if user_id != None:
                async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
                    user_exists = await cursor.fetchone()

                if not user_exists:
                    return JSONResponse(status_code=404,content={"message": f"Пользователь с ID {user_id} не существует."})

                async with db.execute('SELECT * FROM cities WHERE user_id =? AND city_name = ?',  
                                    (user_id, city_request.city_name)) as cursor:
                    existing_city = await cursor.fetchone()
            else:      
                async with db.execute('SELECT * FROM cities WHERE user_id is NULL AND city_name = ?',  
                                    (city_request.city_name,)) as cursor:
                    existing_city = await cursor.fetchone()

            if existing_city:
                return JSONResponse(status_code=200,content={"message": f"Город {city_request.city_name} уже отслеживается."})
            
            await db.execute(
                "INSERT INTO cities (user_id, city_name, latitude, longitude) VALUES (?, ?, ?, ?)", 
                (user_id, city_request.city_name, city_request.latitude, city_request.longitude)
            )
            await db.commit()

            async with db.execute("SELECT last_insert_rowid()") as cursor:
                city_id_row = await cursor.fetchone()
                city_id = city_id_row[0] if city_id_row else None

            try:
                await upd_data_to_db(city_request.city_name)
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": f"Город {city_request.city_name} добавлен, но обновление данных погоды не удалось.",
                        "error": str(e),
                        "city": {
                            "city_id": city_id,
                            "city_name": city_request.city_name,
                            "latitude": city_request.latitude,
                            "longitude": city_request.longitude,
                            "user_id": user_id
                        }
                    }
                )
            return JSONResponse(status_code=201,
                                content={
                                    "message": f"Город {city_request.city_name} успешно добавлен.",
                                    "city": {
                                        "city_id": city_id,
                                        "city_name": city_request.city_name,
                                        "latitude": city_request.latitude,
                                        "longitude": city_request.longitude,
                                        "user_id": user_id
                                            }
                                        })
    except aiosqlite.Error as e:
        return JSONResponse(status_code=500,content={"message": f"Ошибка базы данных: {str(e)}, база {DB_ROUTE}"})
    except Exception as e:
        return JSONResponse(status_code=500,content={"message": f"Неизвестная ошибка: {str(e)}"})
    
@router.get('/cities')
async def cities(user_id: Optional[str] = None):
    """
    Возвращает список городов для пользователя (если указан user_id) или общий список.
    """
    try:
        async with aiosqlite.connect(DB_ROUTE) as db:
            if user_id != None:
                async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
                    user_exists = await cursor.fetchone()

                if not user_exists:
                    return JSONResponse(status_code=404,content={"message": f"Пользователь с ID {user_id} не существует."})

                query = '''
                    SELECT city_name, latitude, longitude
                    FROM cities
                    WHERE user_id = ?
                '''
                async with db.execute(query, (user_id,)) as cursor:
                    cities = await cursor.fetchall()
            else:
                query = '''
                    SELECT city_name, latitude, longitude
                    FROM cities
                    WHERE user_id is NULL
                '''
                async with db.execute(query) as cursor:
                    cities = await cursor.fetchall()
            
            if not cities:
                return JSONResponse(status_code=200,content={"message": "Нет доступных городов для отображения.", "cities": []})
            
            city_list = [
                {"city_name": city[0], "latitude": city[1], "longitude": city[2]} 
                for city in cities
            ]
            return JSONResponse(status_code=200,content={"message": "Список городов успешно получен.", "cities": city_list})
    except aiosqlite.Error as e:
        return JSONResponse(status_code=500,content={"message": f"Ошибка базы данных: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500,content={"message": f"Неизвестная ошибка: {str(e)}"})




@router.get('/{city_name}')
async def city(
    city_name: str = Path(..., description="Название города"),
    user_id: Optional[str] = Query(None, description="ID пользователя (необязательно)"),
    time: str = Query(..., description="Время для прогноза в формате 'HH:MM:SS'"),
    weather_params: Optional[List[str]] = Query(
        ["temperature", "surface_pressure", "wind_speed", "precipitation"],
        description="Параметры погоды, которые нужно вернуть (доступны: температура, влажность, скорость ветра, осадки)"
    )
):
    """
    Возвращает данные города из общего списка городов или из списка пользователя (user_id!=None)
    """
    try:
        async with aiosqlite.connect(DB_ROUTE) as db:
            if user_id!=None:
                async with db.execute('SELECT * FROM users WHERE id = ?', (user_id,)) as cursor:
                    user_exists = await cursor.fetchone()

                if not user_exists:
                    return JSONResponse(status_code=404,content={"message": f"Пользователь с ID {user_id} не существует."})

                query_city = '''
                    SELECT id 
                    FROM cities 
                    WHERE city_name = ? AND user_id = ? 
                '''
                async with db.execute(query_city, (city_name, user_id)) as cursor:
                    city_info = await cursor.fetchone()

            else:
                query_city = '''
                    SELECT id 
                    FROM cities 
                    WHERE city_name = ? AND user_id is NULL
                '''
                async with db.execute(query_city, (city_name,)) as cursor:
                    city_info = await cursor.fetchone()

            if not city_info:
                return JSONResponse(status_code=404, content={"message": f"Город {city_name} не отслеживается"})

            city_id = city_info[0]
            current_date = datetime.now().date()
            query_time = f"{current_date} {time}"

            selected_columns = [param for param in weather_params if param in ["temperature", "surface_pressure", "wind_speed", "precipitation"]]

            if not selected_columns:
                return JSONResponse(status_code=400, content={"message": "Некорректные параметры погоды"})

            query_weather = f'''
                SELECT {", ".join(selected_columns)} 
                FROM weather_data 
                WHERE city_id = ? AND timestamp = ?
            '''
            async with db.execute(query_weather, (city_id, query_time)) as cursor:
                weather_record = await cursor.fetchone()


            if weather_record:
                result = {param: value for param, value in zip(weather_params, weather_record)}
                return JSONResponse(status_code=200, content=result)
            else:
                return JSONResponse(status_code=404, content={"message": f"Данные о погоде в городе {city_name} отсутствуют в базе данных"})

    except aiosqlite.Error as e:
        return JSONResponse(status_code=500, content={"message": f"Ошибка базы данных: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Неизвестная ошибка: {str(e)}"})
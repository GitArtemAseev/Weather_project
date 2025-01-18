import json
from datetime import datetime

import aiosqlite
import aiohttp
from fastapi.responses import JSONResponse

from settings import DB_ROUTE

async def get_weather(params):
    """
    Делает запрос на api.open-meteo.com и возвращает ответ
    """
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.get('https://api.open-meteo.com/v1/forecast', params=params) as resp:
            try:
                if resp.status != 200:
                    return JSONResponse(status_code=resp.status, content={'message': f"Error fetching weather data: {resp.status}"})
                return await resp.text()
            except aiohttp.ClientError as e:
                return JSONResponse(status_code=500, content={'message': f"Request failed: {str(e)}"})


async def upd_data_to_db(city_name=None):
    """
    Обновляет данные всех городов (city=None) или одного города (city = city_name)
    """
    try:
        async with aiosqlite.connect(DB_ROUTE) as db:
            if not city_name:
                async with db.execute('SELECT id, latitude, longitude FROM cities') as cursor:
                    cities = await cursor.fetchall()

            else:
                async with db.execute('SELECT id, latitude, longitude FROM cities WHERE city_name = ? ', (city_name,)) as cursor:
                    cities = await cursor.fetchall()

            for city in cities:
                city_id, latitude, longitude = city
                params = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'minutely_15': 'temperature_2m,surface_pressure,wind_speed_10m,precipitation',
                    'start_date': str(datetime.today().date()),
                    'end_date': str(datetime.today().date())
                }

                weather_data = await get_weather(params)
                weather_data = json.loads(weather_data)

                times = weather_data['minutely_15']['time']
                temperatures = weather_data['minutely_15']['temperature_2m']
                surface_pressures = weather_data['minutely_15']['surface_pressure']
                wind_speeds = weather_data['minutely_15']['wind_speed_10m']
                precipitations = weather_data['minutely_15']['precipitation']

                await db.execute('''DELETE FROM weather_data WHERE city_id = ? AND DATE(timestamp) = ?''', (city_id, datetime.today().date()))

                for time, temperature, surface_pressure, wind_speed, precipitation in zip(
                    times, temperatures, surface_pressures, wind_speeds, precipitations
                ):
                    forecast_time = datetime.fromisoformat(time)
                    await db.execute('''
                        INSERT INTO weather_data (city_id, timestamp, temperature, surface_pressure, wind_speed, precipitation)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (city_id, forecast_time, temperature, surface_pressure, wind_speed, precipitation))

            await db.commit()
            if city_name:
                print(f'Данные погоды в городе {city_name} добавлены')
            else:
                print(f'Данные погоды во всех отслеживаемых городах обновлены')

    except Exception as e:
        print(f"Ошибка при обновлении данных в базе: {e}")
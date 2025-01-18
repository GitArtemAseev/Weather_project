from datetime import datetime

import pytest
import aiosqlite
from fastapi.testclient import TestClient

from conftest import DB_ROUTE
from script import app


client = TestClient(app)

@pytest.mark.asyncio
async def test_add_city():
    try:
        response = client.post(
            "/cities/add_city",
            json={
                "city_name": "Moscow",
                "latitude": 55.7558,
                "longitude": 37.6173
            },
        )

        assert response.status_code == 201, f"Ожидался статус 404, но получен {response.status_code}"
        assert response.json()["message"] == "Город Moscow успешно добавлен."
    except Exception as e:
        print(f"Ошибка в тесте 'test_add_city': {e}")
        raise

@pytest.mark.asyncio
async def test_get_city_weather():
    try:
        city_name = 'Novocherkask'
        response = client.post(
            "/cities/add_city",
            json={
                "city_name": city_name,
                "latitude": 55.7558,
                "longitude": 37.6173
            },
        )
        assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}"
        data = response.json()
        assert data["message"] == f"Город {city_name} успешно добавлен."

        city_id = data["city"]["city_id"]
        assert city_id is not None, "Не удалось получить city_id из ответа"

        current_date = datetime.now().date()
        timestamp_str = f"{current_date} 10:00:00"

        async with aiosqlite.connect(DB_ROUTE) as db:
            await db.execute(
                """
                INSERT INTO weather_data 
                (city_id, timestamp, temperature, surface_pressure, wind_speed, precipitation)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (city_id, timestamp_str, 20.5, 5.0, 10.0, 20.9)
            )
            await db.commit()

        response = client.get(
            f"/cities/{city_name}?time=10:00:00&weather_params=temperature&weather_params=wind_speed"
        )
        assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}"
        weather_data = response.json()

        assert "temperature" in weather_data, "Параметр 'temperature' отсутствует в ответе"
        assert "wind_speed" in weather_data,  "Параметр 'wind_speed' отсутствует в ответе"

    except Exception as e:
        print(f"Ошибка в тесте 'test_get_city_weather': {e}")
        raise


@pytest.mark.asyncio
async def test_register_user():
    try:
        response = client.post(
            "/users/register",
            params={"name": "NewUser"}
        )
        assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}"
        assert "id" in response.json(), "ID пользователя не найден"
        assert response.json()["message"] == "Пользователь зарегистрирован", "Сообщение о регистрации неверное"
    except Exception as e:
        print(f"Ошибка в тесте 'test_register_user': {e}")
        raise


@pytest.mark.asyncio
async def test_invalid_weather_param():
    try:
        city_name = "Moscow"
        time = "10:00:00"

        response = client.get(
            f"/cities/{city_name}?time={time}&weather_params=invalid_param"
        )
        assert response.status_code == 400, f"Ожидался статус 400, но получен {response.status_code}"
        data = response.json()
        assert "Некорректные параметры погоды" in data["message"]
    except Exception as e:
        print(f"Ошибка в тесте 'test_invalid_weather_param': {e}")
        raise

@pytest.mark.asyncio
async def test_add_city_user_not_exists():
    try:
        undefined_user_id = 9999 

        response = client.post(
            "/cities/add_city",
            params={"user_id": undefined_user_id},
            json={
                "city_name": "NonExistentCity",
                "latitude": 55.7558,
                "longitude": 37.6173
            },
        )

        assert response.status_code == 404, f"Ожидался статус 404, но получен {response.status_code}"
        
        assert response.json()["message"] == f"Пользователь с ID {undefined_user_id} не существует.", \
            "Некорректное сообщение об ошибке при отсутствии пользователя"

    except Exception as e:
        print(f"Ошибка в тесте 'test_add_city_user_not_exists': {e}")
        raise

@pytest.mark.asyncio
async def test_no_city_found():
    try:
        city_name = "UnknownCity"
        user_id = 1
        time = "10:00:00"

        response = client.get(
            f"/cities/{city_name}?user_id={user_id}&time={time}&weather_params=temperature"
        )
        assert response.status_code == 404, f"Ожидался статус 404, но получен {response.status_code}"
        data = response.json()
        assert f"Город {city_name} не отслеживается" in data["message"]
    except Exception as e:
        print(f"Ошибка в тесте 'test_no_city_found': {e}")
        raise

@pytest.mark.asyncio
async def test_get_cities():
    try:
        response = client.get("/cities/cities")
        assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}"
        data = response.json()
        assert isinstance(data["cities"], list), "Ответ 'cities' должен быть списком"
    except Exception as e:
        print(f"Ошибка в тесте 'test_get_cities': {e}")
        raise

@pytest.mark.asyncio
async def test_add_city_missing_params():
    try:
        response = client.post(
            "/cities/add_city",
            json={},
        )
        assert response.status_code == 422, f"Ожидался статус 422, но получен {response.status_code}"
        assert "detail" in response.json(), "Сообщение об ошибке не найдено"
    except Exception as e:
        print(f"Ошибка в тесте 'test_add_city_missing_params': {e}")
        raise

@pytest.mark.asyncio
async def test_add_city_invalid_coordinates():
    try:
        response = client.post(
            "/cities/add_city",
            json={
                "city_name": "TestCity",
                "latitude": 200.0, 
                "longitude": 300.0  
            },
        )
        assert response.status_code == 422, f"Ожидался статус 422, но получен {response.status_code}"
        assert "detail" in response.json(), "Сообщение об ошибке не найдено"
    except Exception as e:
        print(f"Ошибка в тесте 'test_add_city_invalid_coordinates': {e}")
        raise

@pytest.mark.asyncio
async def test_add_city_already_exists():
    try:

        response = client.post("/cities/add_city",
            json={
                "city_name": "Samara",
                "latitude": 55.7558,
                "longitude": 37.6173
            },
        )
        assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}"
        
        response = client.post("/cities/add_city",
            json={
                "city_name": "Samara",
                "latitude": 55.7558,
                "longitude": 37.6173
            },
        )
        assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}"
        assert response.json()["message"] == "Город Samara уже отслеживается."
    except Exception as e:
        print(f"Ошибка в тесте 'test_add_city_already_exists': {e}")
        raise

@pytest.mark.asyncio
async def test_get_city_weather_invalid_time():
    try:
        city_name = "Moscow"
        invalid_time = "invalid_time_format"

        response = client.get(
            f"/cities/{city_name}?time={invalid_time}&weather_params=temperature&weather_params=wind_speed"
        )
        assert response.status_code == 404, f"Ожидался статус 404, но получен {response.status_code}"
        assert "message" in response.json()
    except Exception as e:
        print(f"Ошибка в тесте 'test_get_city_weather_invalid_time': {e}")
        raise

@pytest.mark.asyncio
async def test_get_city_weather_no_data():
    try:
        city_name = "Moscow"
        time = "23:59:59"
        response = client.get(f"/cities/{city_name}?time={time}&weather_params=temperature&weather_params=wind_speed")

        assert response.status_code == 404, f"Ожидался статус 404, но получен {response.status_code}"
        assert f"Данные о погоде в городе {city_name} отсутствуют в базе данных" in response.json()["message"]

    except Exception as e:
        print(f"Ошибка в тесте 'test_get_city_weather_no_data': {e}")
        raise

@pytest.mark.asyncio
async def test_get_cities_for_user():
    try:

        response = client.post("/cities/add_city?user_id=1",
            json={
                "city_name": "Omsk",
                "latitude": 55.7558,
                "longitude": 37.6173
                },)
        assert response.status_code == 201, f"Ожидался статус 201, но получен {response.status_code}"

        response = client.get("/cities/cities?user_id=1")
        assert response.status_code == 200, f"Ожидался статус 200, но получен {response.status_code}"
        data = response.json()
        assert isinstance(data["cities"], list), "Ответ 'cities' должен быть списком"
        assert len(data["cities"]) > 0, "Список городов пуст"
    except Exception as e:
        print(f"Ошибка в тесте 'test_get_cities_for_user': {e}")
        raise


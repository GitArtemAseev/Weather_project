## Проект требует установленный python Версии 3.10.5

## Установка и запуск

**Windows** 

Откройте командную строку (CMD) или PowerShell и перейдите в корневую директорию проекта. Затем выполните:
python -m venv venv

Затем активируйте виртуальное окружение venv:
venv\Scripts\activate

Установите все зависимости выполнив команду:
pip install -r requirements.txt

Запустите проект командой:
python script.py

Для запуска тестов используйте команду:
pytest


**Linux/MacOS**

Откройте терминал и перейдите в корневую директорию проекта. Затем выполните:
python3 -m venv venv

Затем активируйте виртуальное окружение venv:
source venv/bin/activate

Установите все зависимости выполнив команду:
pip install -r requirements.txt

Запустите проект командой:
python3 script.py

Для запуска тестов используйте команду:
pytest


## Настройка
В проекте имеется файл settings.py, который отвечает за конфигурацию приложения. В нем определены две переменные:

DB_ROUTE: Путь до базы данных.
REFRESH_TIME: Частота обновления данных о погоде (в минутах).

Они достаются из .env, если такого файла не будет создано, то берутся стандартные значения - 15 минут и "weather.db".



## Описание сервисов:

**app/db.py**
**async def init_db(DB_ROUTE) -> None**

Создаёт и инициализирует базу данных SQLite, если она ещё не существует.
Определяет и создаёт три таблицы:
users: хранит записи о пользователях (id, name).
cities: хранит записи о городах (id, city_name, широта, долгота, user_id).
weather_data: хранит записи о погоде (id, city_id, timestamp, temperature, surface_pressure, wind_speed, precipitation).

Как работает:
Открывает соединение с базой данных через aiosqlite.
Проверяет/создаёт структуры таблиц с помощью CREATE TABLE IF NOT EXISTS.
Фиксирует (commit) изменения в базе.
Если при инициализации что-то пошло не так, печатает ошибку и выбрасывает исключение, чтобы не продолжать работу с некорректной базой.

Вызывается перед запуском приложения


**app/service.py**
**async def get_weather(params) -> str | JSONResponse**

Отправляет HTTP-запрос к внешнему API Open-Meteo, используя переданные params.
Возвращает ответ в виде текста (str) от api.open-meteo.com, либо, в случае ошибки, формирует объект JSONResponse с описанием проблемы.

Как работает:
Открывает асинхронную сессию aiohttp.ClientSession (с таймаутом 10 секунд).
Делает GET-запрос к https://api.open-meteo.com/v1/forecast с помощью переданных параметров params.
Если статус ответа не 200, возвращает JSONResponse с информацией об ошибке.
Иначе — получает содержимое ответа с помощью await resp.text().
Если во время запроса возникает aiohttp.ClientError, возвращает JSONResponse с сообщением об ошибке.


**app/service.py**
**async def upd_data_to_db(city_name: str | None = None) -> None**

Обновляет данные о погоде в таблице weather_data для:
Всех городов, если city_name не указан (None).
Одного конкретного города, если city_name указан.

Как работает:
Получение списка городов:
Если city_name не передан, выбирает все записи из таблицы cities.
Если city_name есть, выбирает запись только для этого города.
Для каждого города:
Формирует словарь params с координатами (latitude, longitude), а также дополнительными параметрами для api.open-meteo.com (например, minutely_15, даты начала и конца запроса).
Вызывает get_weather(params) для получения данных в формате JSON.
Парсит ответ (через json.loads(weather_data)).
Извлекает списки времени time, температуры temperature_2m, давления surface_pressure и т.д. из секции minutely_15.
Удаляет из weather_data старые записи за текущую дату DATE(timestamp) = текущая дата, чтобы не плодить дубли.
Построчно вставляет новые данные в таблицу weather_data, указывая:
city_id — идентификатор города из таблицы cities.
timestamp — сформированное значение времени (конвертация datetime.fromisoformat(time)).
temperature, surface_pressure, wind_speed, precipitation и пр.
Сохраняет изменения (commit) в базе.

Вызывается при добавлении нового города (чтобы сразу получить актуальные данные).
Вызывается периодически (через планировщик) для обновления данных о погоде во всех городах.


## Описание эндпоинтов:

**GET /weather/current**
Возвращает информацию о текущей погоде по переданным координатам, используя внешнее API Open-Meteo.

Параметры:
latitude: float (query, обязательный) — широта точки, для которой нужна погода.
longitude: float (query, обязательный) — долгота точки.

Формирует params для запроса к api.open-meteo.com.
Вызывает get_weather(params), которое отправляет запрос к внешнему сервису.
Если ответ содержит ключ 'current', извлекает temperature_2m, wind_speed_10m, surface_pressure.
Возвращает JSONResponse со статусом 200 и объектом вида:

{
  "temperature": 20.5,
  "wind_speed": 5.3,
  "surface_pressure": 1015.2
}
Если что-то пошло не так (например, current не найден), возвращает статусы 404 или 500 с описанием проблемы.


**POST /users/register**
Регистрирует пользователя по имени или возвращает уже существующего, если имя совпадает с ранее созданным.

Параметры:
name: str (query, обязательный) — имя пользователя.

Проверяет, есть ли уже пользователь с таким именем в таблице users.
Если да, возвращает статус 200 и сообщение "Пользователь уже существует", вместе с id найденного пользователя.
Если нет, добавляет новую запись в users и возвращает статус 201 с сообщением "Пользователь зарегистрирован" и id нового пользователя.

{
  "message": "Пользователь зарегистрирован",
  "id": 1
}


**POST /cities/add_city или /cities/add_city?user_id={user_id}**
Добавляет новый город в базу данных

Если user_id передан, то город будет принадлежать конкретному пользователю.
Если user_id не передан, город считается «общим» (user_id = NULL в таблице).

Тело запроса:

{
  "city_name": str,
  "latitude": float,
  "longitude": float
}

city_name — название города (обязательно).
latitude — широта (число, в диапазоне -90..90).
longitude — долгота (число, в диапазоне -180..180).

Query параметр:
user_id (необязательный): ID пользователя. Если не передан, город будет «общим».

Если указан user_id, проверяется, существует ли такой пользователь. Если нет, вернёт статус 404.
Если город уже существует у пользователя или в общем списке (при отсутствии user_id), вернётся статус 200 и сообщение: «Город уже отслеживается.»
В противном случае:
Город вставляется в таблицу cities.
Вызывается upd_data_to_db(city_request.city_name), чтобы сразу обновить данные погоды для этого города.
Возвращается статус 201 и подробная информация о созданном городе.


**GET /cities/cities или /cities/cities?user_id={user_id}**
Возвращает список городов либо для определённого пользователя, либо общий список (если пользователь не указан).

Query-параметр:
user_id (необязательный): Если указан, возвращает только города этого пользователя. Если отсутствует, возвращаются города с user_id = NULL.

Если user_id задан, проверяется, существует ли пользователь:
Если пользователя нет, вернёт статус 404.
Иначе возвращает все города с cities.user_id = user_id.
Если user_id не задан, возвращает все города с user_id IS NULL.
Если города отсутствуют, вернёт статус 200 с сообщением «Нет доступных городов для отображения.» и пустым списком.
При наличии городов вернёт статус 200 и список вида:
{
  "message": "Список городов успешно получен.",
  "cities": [
    {
      "city_name": str,
      "latitude": float,
      "longitude": float
    },
    ...
  ]
}


**GET /cities/{city_name}?time={time} или /cities/{city_name}?user_id={user_id}&time={time}**
Возвращает данные о погоде для города city_name

Проверяет, является ли город общим (если user_id не указан) либо принадлежащим пользователю (если user_id указан).
Затем ищет записи о погоде (за сегодняшний день и конкретное time).

Query-параметры:
user_id: Optional[str]: ID пользователя (необязательно).
time: str (обязательно): Время в формате HH:MM:SS.
weather_params: Optional[List[str]]: Параметры погоды, которые нужно вернуть, например: temperature, surface_pressure, wind_speed, precipitation.
Если weather_params не передан, то по умолчанию передаются все 4 параметра


Если передан user_id, проверяется, существует ли пользователь. Если нет, ответит статусом 404.
Определяется city_id по сочетанию (city_name, user_id).
Если не найден, возвращает статус 404 с сообщением «Город {city_name} не отслеживается.»
Генерируется query_time, добавляя к текущей дате datetime.now().date() время из time.
Из списка параметров weather_params фильтруются только допустимые значения (["temperature", "surface_pressure", "wind_speed", "precipitation"]).
Выполняется запрос к таблице weather_data.
Если запись найдена, возвращает статус 200 и словарь с выбранными погодными параметрами. Иначе — статус 404 с сообщением, что данных о погоде нет.

Пример
{
  "temperature": 18.2,
  "wind_speed": 3.4
}


## Тесты

Тесты запускаются из корневой папки командой pytest.
Хранятся же они в папке tests.

tests/conftest.py - конфигурационный файл
tests/weather_test.py - тесты эндпоинта /weather/current
tests/func_with_bd_test.py - тесты остальных эндпоинтов которые связаны с бд
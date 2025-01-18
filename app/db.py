import aiosqlite

async def init_db(DB_ROUTE):
    """
    Инициализирует БД
    """
    async with aiosqlite.connect(DB_ROUTE) as db:
        try:
            await db.execute('''CREATE TABLE IF NOT EXISTS users (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT NOT NULL
                                 )''')
            
            await db.execute('''CREATE TABLE IF NOT EXISTS cities (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    city_name TEXT NOT NULL,
                                    latitude REAL NOT NULL,
                                    longitude REAL NOT NULL,
                                    user_id INTEGER,
                                    FOREIGN KEY(user_id) REFERENCES users(id)
                                 )''')

            await db.execute('''CREATE TABLE IF NOT EXISTS weather_data (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    city_id INTEGER NOT NULL,
                                    timestamp DATETIME NOT NULL,
                                    temperature REAL,
                                    surface_pressure REAL,
                                    wind_speed REAL,
                                    precipitation REAL,
                                    FOREIGN KEY(city_id) REFERENCES cities(id)
                                 )''')
            print("Таблица 'weather_data' успешно создана или уже существует.")

            await db.commit()

        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")
            raise


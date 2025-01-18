import os

DB_ROUTE = os.getenv("DB_ROUTE", "weather.db")
REFRESH_TIME = int(os.getenv("REFRESH_TIME", 15))

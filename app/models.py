from pydantic import BaseModel,Field

class CityRequest(BaseModel):
    """
    Структура json для /add_city
    """
    city_name: str = Field(..., description="Название города")
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Широта (от -90 до 90)"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Долгота (от -180 до 180)"
    )
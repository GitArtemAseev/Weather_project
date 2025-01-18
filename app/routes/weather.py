import json

import aiohttp
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.service import get_weather


router = APIRouter()

@router.get('/current')
async def get_weather_by_coords(latitude: float = Query(..., description="Широта"),
                                longitude: float = Query(..., description="Долгота")):
    """
    С помощью get_weather возвращает погоду по координатам
    """
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': 'temperature_2m,surface_pressure,wind_speed_10m',
    }

    try:
        response = await get_weather(params)
        response = json.loads(response)

        if 'current' not in response:
            return JSONResponse(status_code=404, content={'message': "Current weather data not found"})

        temperature = response['current']['temperature_2m']
        wind_speed = response['current']['wind_speed_10m']
        surface_pressure = response['current']['surface_pressure']
        
        weather_data = {
            'temperature': temperature,
            'wind_speed': wind_speed,
            'surface_pressure': surface_pressure
        }
        return JSONResponse(status_code=200, content=weather_data)

    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={'message': "Failed to decode the response from the weather service"})
    
    except aiohttp.ClientError as e:
        return JSONResponse(status_code=500, content={'message': f"Request to weather service failed: {str(e)}"})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={'message': f"An unexpected error occurred: {str(e)}"})
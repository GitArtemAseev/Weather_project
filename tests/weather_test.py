import asyncio

import pytest
from fastapi.testclient import TestClient

from script import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_weather_by_coords_success():

    response = await asyncio.to_thread(client.get, '/weather/current?latitude=55.7558&longitude=37.6176')
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'temperature' in json_data
    assert 'wind_speed' in json_data
    assert 'surface_pressure' in json_data
    
    assert isinstance(json_data['temperature'], (int, float))
    assert isinstance(json_data['wind_speed'], (int, float))
    assert isinstance(json_data['surface_pressure'], (int, float))



@pytest.mark.asyncio
async def test_get_weather_invalid_coordinates():
    response = await asyncio.to_thread(client.get, '/weather/current?latitude=invalid&longitude=37.6176')

    
    assert response.status_code == 422  
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_weather_missing_parameters():
    response = await asyncio.to_thread(client.get, '/weather/current')
    
    assert response.status_code == 422  
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_get_weather_out_of_bounds_coordinates():
    response = client.get('/weather/current?latitude=1000&longitude=2000') 
    
    assert response.status_code == 500
    assert "message" in response.json()


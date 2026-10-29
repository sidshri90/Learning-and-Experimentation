from fastapi import Request

from app.services.geocoding import GeocodingProvider
from app.services.weather import WeatherService


def get_geocoder(request: Request) -> GeocodingProvider:
    return request.app.state.geocoder


def get_weather_service(request: Request) -> WeatherService:
    return request.app.state.weather

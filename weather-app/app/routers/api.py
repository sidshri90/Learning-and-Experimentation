from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.deps import get_geocoder, get_weather_service
from app.models import Location, Units, WeatherReport
from app.services.geocoding import GeocodingProvider
from app.services.weather import WeatherService

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/locations/suggest", response_model=list[Location])
async def suggest_locations(
    q: str = Query("", max_length=100),
    geocoder: GeocodingProvider = Depends(get_geocoder),
    settings: Settings = Depends(get_settings),
) -> list[Location]:
    if len(q.strip()) < settings.suggest_min_chars:
        return []
    return await geocoder.suggest(q.strip(), settings.suggest_limit)


@router.get("/weather", response_model=WeatherReport)
async def weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    units: Units = Units.metric,
    service: WeatherService = Depends(get_weather_service),
) -> WeatherReport:
    return await service.get_report(lat, lon, units)

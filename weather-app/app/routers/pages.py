from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings
from app.deps import get_geocoder, get_weather_service
from app.errors import UpstreamError
from app.models import Units
from app.services.geocoding import GeocodingProvider
from app.services.weather import WeatherService
from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, settings: Settings = Depends(get_settings)):
    return templates.TemplateResponse(request, "index.html", {"settings": settings})


# Partial routes return 200 even on upstream failure: HTMX does not swap 4xx/5xx
# responses by default, and the error message is part of the UI.


@router.get("/partials/suggest", response_class=HTMLResponse)
async def suggest(
    request: Request,
    q: str = Query("", max_length=100),
    geocoder: GeocodingProvider = Depends(get_geocoder),
    settings: Settings = Depends(get_settings),
):
    query = q.strip()
    searched = len(query) >= settings.suggest_min_chars
    locations, error = [], None
    if searched:
        try:
            locations = await geocoder.suggest(query, settings.suggest_limit)
        except UpstreamError as exc:
            error = exc.message
    return templates.TemplateResponse(
        request,
        "partials/suggestions.html",
        {"locations": locations, "query": query, "searched": searched, "error": error},
    )


@router.get("/partials/weather", response_class=HTMLResponse)
async def weather(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    name: str = Query("", max_length=200),
    units: Units = Units.metric,
    service: WeatherService = Depends(get_weather_service),
):
    ctx = {"lat": lat, "lon": lon, "name": name, "units": units.value}
    try:
        report = await service.get_report(lat, lon, units)
    except UpstreamError as exc:
        return templates.TemplateResponse(
            request, "partials/error.html", {**ctx, "message": exc.message}
        )
    return templates.TemplateResponse(request, "partials/weather.html", {**ctx, "report": report})

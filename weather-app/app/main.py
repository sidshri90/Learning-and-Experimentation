import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.cache import AsyncTTLCache
from app.config import get_settings
from app.errors import UpstreamError
from app.routers import api, pages
from app.services.geocoding import OpenMeteoGeocoder
from app.services.weather import WeatherService
from app.templating import BASE_DIR

logger = logging.getLogger("weather")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """One shared HTTP client and cache set for the whole process."""
    async with httpx.AsyncClient(
        timeout=settings.http_timeout, headers={"User-Agent": "weather-app/0.2"}
    ) as client:
        app.state.geocoder = OpenMeteoGeocoder(
            client, AsyncTTLCache(settings.cache_maxsize, settings.geocode_cache_ttl), settings.geocoding_url
        )
        app.state.weather = WeatherService(
            client, AsyncTTLCache(settings.cache_maxsize, settings.forecast_cache_ttl), settings.forecast_url
        )
        yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(pages.router)
app.include_router(api.router)


@app.exception_handler(UpstreamError)
async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    """JSON API routes report upstream failures as 502."""
    return JSONResponse({"detail": exc.message}, status_code=502)


if not Path(BASE_DIR / "static/vendor/htmx.min.js").exists():
    logger.warning("htmx.min.js is missing. Run: python scripts/fetch_htmx.py")

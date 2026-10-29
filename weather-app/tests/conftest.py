from types import SimpleNamespace

import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

PARIS = {
    "results": [
        {"id": 1, "name": "Paris", "latitude": 48.85, "longitude": 2.35, "country": "France",
         "country_code": "FR", "admin1": "Île-de-France", "population": 2138551, "timezone": "Europe/Paris"},
        {"id": 2, "name": "Paris", "latitude": 33.66, "longitude": -95.56, "country": "United States",
         "country_code": "US", "admin1": "Texas", "population": 24912, "timezone": "America/Chicago"},
        {"id": 3, "name": "Paris", "latitude": 36.30, "longitude": -88.32, "country": "United States",
         "country_code": "US", "admin1": "Tennessee", "population": 10156, "timezone": "America/Chicago"},
    ]
}


def forecast_payload(**current_overrides):
    current = {
        "time": "2026-10-28T14:15", "temperature_2m": 31.4, "relative_humidity_2m": 62,
        "apparent_temperature": 34.6, "is_day": 1, "weather_code": 2,
        "wind_speed_10m": 12.2, "wind_direction_10m": 95, "pressure_msl": 1009.6,
    }
    current.update(current_overrides)
    return {
        "timezone": "Asia/Kolkata",
        "current": current,
        "daily": {
            "time": ["2026-10-28", "2026-10-29", "2026-10-30"],
            "weather_code": [2, 61, 95],
            "temperature_2m_max": [32.1, 30.4, 29.6],
            "temperature_2m_min": [22.0, 21.5, 20.8],
            "precipitation_probability_max": [10, 55, None],
            "sunrise": ["2026-10-28T05:42", "2026-10-29T05:43", "2026-10-30T05:44"],
            "sunset": ["2026-10-28T17:05", "2026-10-29T17:04", "2026-10-30T17:03"],
            "uv_index_max": [7.9, 6.0, 5.1],
        },
        "hourly": {
            "time": ["2026-10-28T13:00", "2026-10-28T14:00", "2026-10-28T15:00"],
            "visibility": [24140.0, 10000.0, 9000.0],
            "uv_index": [5.2, 3.44, 2.1],
        },
    }


@pytest.fixture
def api():
    """Mocked Open-Meteo endpoints (no real network calls in tests)."""
    with respx.mock(assert_all_called=False) as mock:
        yield SimpleNamespace(
            geo=mock.get(GEO_URL).respond(json=PARIS),
            forecast=mock.get(FORECAST_URL).respond(json=forecast_payload()),
        )


@pytest.fixture
def client(api):
    with TestClient(app) as c:  # the context manager runs the app lifespan
        yield c

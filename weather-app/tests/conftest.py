from types import SimpleNamespace

import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

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


def _hourly():
    """48 hourly points from 2026-10-28T00:00. Index 14 (14:00) is the 'current' hour."""
    times = [f"2026-10-{28 + h // 24}T{h % 24:02d}:00" for h in range(48)]
    visibility, uv = [24140.0] * 48, [0.0] * 48
    visibility[14], uv[14] = 10000.0, 3.44
    return {
        "time": times,
        "visibility": visibility,
        "uv_index": uv,
        "temperature_2m": [20 + (h % 12) + 0.4 for h in range(48)],
        "weather_code": [2] * 48,
        "precipitation_probability": [h % 7 * 10 for h in range(48)],
        "wind_speed_10m": [10 + h % 5 + 0.2 for h in range(48)],
        "is_day": [1 if 6 <= h % 24 < 18 else 0 for h in range(48)],
    }


def aq_payload(us_aqi=162, **overrides):
    cur = {"time": "2026-10-28T14:00", "interval": 3600, "us_aqi": us_aqi, "pm10": 88.34, "pm2_5": 61.21}
    cur.update(overrides)
    return {"current": cur}


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
        "hourly": _hourly(),
    }


@pytest.fixture
def api():
    """Mocked Open-Meteo endpoints (no real network calls in tests)."""
    with respx.mock(assert_all_called=False) as mock:
        yield SimpleNamespace(
            geo=mock.get(GEO_URL).respond(json=PARIS),
            forecast=mock.get(FORECAST_URL).respond(json=forecast_payload()),
            aq=mock.get(AQ_URL).respond(json=aq_payload()),
        )


@pytest.fixture
def client(api):
    with TestClient(app) as c:  # the context manager runs the app lifespan
        yield c

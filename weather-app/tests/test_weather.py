import asyncio

import httpx
import pytest
import respx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import Units
from app.services.weather import WeatherService, parse_forecast
from tests.conftest import FORECAST_URL, forecast_payload


def test_parse_forecast_normalizes_values():
    report = parse_forecast(forecast_payload(), Units.metric, 25.59, 85.14)
    assert report.temp_unit == "°C" and report.wind_unit == "km/h"
    assert report.observed_time == "14:15"
    c = report.current
    assert (c.temperature, c.feels_like, c.humidity, c.wind_speed) == (31, 35, 62, 12)
    assert c.wind_compass == "E" and c.description == "Partly cloudy"
    assert [d.high for d in report.daily] == [32, 30, 30]
    assert [d.precipitation_chance for d in report.daily] == [10, 55, None]
    assert report.daily[2].description == "Thunderstorm"


def test_night_uses_night_icon():
    report = parse_forecast(forecast_payload(is_day=0, weather_code=0), Units.metric, 0, 0)
    assert report.current.icon == "🌙"


def test_malformed_payload_raises_upstream_error():
    with pytest.raises(UpstreamError):
        parse_forecast({"current": {}}, Units.metric, 0, 0)
    bad = forecast_payload()
    bad["daily"]["temperature_2m_max"][1] = None
    with pytest.raises(UpstreamError):
        parse_forecast(bad, Units.metric, 0, 0)



def run_report(*calls):
    """calls: (lat, lon, units) tuples run against one service instance."""

    async def go():
        async with httpx.AsyncClient() as client:
            svc = WeatherService(client, AsyncTTLCache(10, 60), FORECAST_URL)
            return [await svc.get_report(*c) for c in calls]

    return asyncio.run(go())


def test_units_are_sent_to_provider():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(FORECAST_URL).respond(json=forecast_payload())
        run_report((25.5941, 85.1376, Units.imperial))
    params = route.calls.last.request.url.params
    assert params["temperature_unit"] == "fahrenheit" and params["wind_speed_unit"] == "mph"
    assert params["latitude"] == "25.59" and params["timezone"] == "auto"


def test_cache_is_per_location_and_units():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(FORECAST_URL).respond(json=forecast_payload())
        run_report((25.59, 85.13, Units.metric), (25.591, 85.134, Units.metric))
        assert route.call_count == 1  # rounds to the same point
        run_report((25.59, 85.13, Units.imperial))
        assert route.call_count == 2  # different units, new cache instance anyway


def test_http_failure_raises_upstream_error():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(FORECAST_URL).respond(503)
        with pytest.raises(UpstreamError):
            run_report((1, 2, Units.metric))

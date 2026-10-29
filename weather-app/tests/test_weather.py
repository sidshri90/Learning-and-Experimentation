import asyncio

import httpx
import pytest
import respx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import Units
from app.services.weather import WeatherService, parse_forecast
from app.services.air_quality import AirQualityService
from tests.conftest import AQ_URL, FORECAST_URL, aq_payload, forecast_payload


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


def test_parse_forecast_extra_readings_metric():
    report = parse_forecast(forecast_payload(), Units.metric, 25.59, 85.14)
    c = report.current
    assert c.wind_direction == 95
    assert c.pressure == 1010 and report.pressure_unit == "hPa"
    assert c.visibility == 10.0 and report.visibility_unit == "km"  # read at the 14:00 hour
    assert c.uv_index == 3.4 and c.uv_category == "Moderate"
    assert report.sunrise == "05:42" and report.sunset == "17:05"
    assert report.uv_max == 7.9


def test_parse_forecast_extra_readings_imperial():
    report = parse_forecast(forecast_payload(), Units.imperial, 25.59, 85.14)
    assert report.current.pressure == 29.81 and report.pressure_unit == "inHg"
    assert report.current.visibility == 6.2 and report.visibility_unit == "mi"


def test_missing_optional_data_does_not_fail():
    data = forecast_payload()
    del data["hourly"]
    del data["current"]["pressure_msl"]
    del data["current"]["wind_direction_10m"]
    for key in ("sunrise", "sunset", "uv_index_max"):
        del data["daily"][key]
    report = parse_forecast(data, Units.metric, 0, 0)
    c = report.current
    assert c.pressure is None and c.visibility is None and c.uv_index is None and c.uv_category is None
    assert c.wind_direction is None and c.wind_compass is None
    assert report.sunrise is None and report.sunset is None and report.uv_max is None


def test_hour_without_matching_hourly_entry_gives_none():
    report = parse_forecast(forecast_payload(time="2026-11-05T20:15"), Units.metric, 0, 0)
    assert report.current.visibility is None and report.current.uv_index is None
    assert report.hourly == []


def test_hourly_strip_is_24_hours_from_now_with_sun_markers_in_order():
    strip = parse_forecast(forecast_payload(), Units.metric, 0, 0).hourly
    hours = [h for h in strip if h.kind == "hour"]
    suns = [(h.label, h.time) for h in strip if h.kind == "sun"]
    assert len(hours) == 24
    assert hours[0].label == "Now" and hours[0].time == "14:00"
    assert hours[-1].time == "13:00"  # 14:00 today .. 13:00 tomorrow
    # today's sunrise (05:42) is already past; tomorrow's sunset (17:04) is beyond the window
    assert suns == [("Sunset", "17:05"), ("Sunrise", "05:43")]
    times = [h.time for h in strip]
    i = times.index("17:05")
    assert times[i - 1] == "17:00" and times[i + 1] == "18:00"  # marker sits between its hours
    # fixture values at 14:00: 20 + (14 % 12) + 0.4 = 22.4 deg, wind 10 + 14 % 5 + 0.2 = 14.2, rain 14 % 7 * 10 = 0
    assert strip[0].temperature == 22 and strip[0].wind_speed == 14 and strip[0].precipitation_chance == 0
    assert hours[0].icon == "⛅" and hours[4].time == "18:00" and hours[4].icon == "☁️"  # day vs night icon


def test_hourly_strip_failure_is_not_fatal():
    data = forecast_payload()
    data["hourly"]["weather_code"] = [None] * 48
    data["hourly"]["temperature_2m"] = "garbage"
    report = parse_forecast(data, Units.metric, 0, 0)
    assert report.current.temperature == 31  # rest of the report is intact


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
    assert "pressure_msl" in params["current"]
    assert {"visibility", "uv_index", "temperature_2m", "is_day"} <= set(params["hourly"].split(","))
    assert "sunrise" in params["daily"] and "uv_index_max" in params["daily"]


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


def run_with_air(*calls):
    async def go():
        async with httpx.AsyncClient() as client:
            aq = AirQualityService(client, AsyncTTLCache(10, 60), AQ_URL)
            svc = WeatherService(client, AsyncTTLCache(10, 60), FORECAST_URL, aq)
            return [await svc.get_report(*c) for c in calls]

    return asyncio.run(go())


def test_report_includes_air_quality():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(FORECAST_URL).respond(json=forecast_payload())
        aq_route = mock.get(AQ_URL).respond(json=aq_payload())
        (report,) = run_with_air((25.59, 85.14, Units.metric))
    assert report.air_quality.aqi == 162 and report.air_quality.category == "Unhealthy"
    assert aq_route.calls.last.request.url.params["current"] == "us_aqi,pm10,pm2_5"


def test_air_quality_failure_does_not_break_forecast_and_is_not_cached():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(FORECAST_URL).respond(json=forecast_payload())
        aq_route = mock.get(AQ_URL).respond(500)
        first, second = run_with_air((1, 2, Units.metric), (1, 2, Units.metric))
    assert first.air_quality is None and first.current.temperature == 31
    assert aq_route.call_count == 2  # the failure was retried, not cached


def test_air_quality_is_shared_between_unit_systems():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(FORECAST_URL).respond(json=forecast_payload())
        aq_route = mock.get(AQ_URL).respond(json=aq_payload())
        run_with_air((1, 2, Units.metric), (1, 2, Units.imperial))
    assert aq_route.call_count == 1

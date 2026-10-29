from typing import Any

import httpx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import CurrentConditions, DailyForecast, Units, WeatherReport
from app.services.scales import hpa_to_inhg, m_to_km, m_to_mi, uv_category
from app.services.wmo import compass, describe

_CURRENT = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,"
    "wind_speed_10m,wind_direction_10m,pressure_msl"
)
_DAILY = (
    "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
    "sunrise,sunset,uv_index_max"
)
_HOURLY = "visibility,uv_index"  # read at the current hour; milestone 5 adds the 24 h strip

_UNIT_PARAMS = {
    Units.metric: {"temperature_unit": "celsius", "wind_speed_unit": "kmh"},
    Units.imperial: {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph"},
}
_LABELS = {  # temperature, wind, pressure, visibility
    Units.metric: ("°C", "km/h", "hPa", "km"),
    Units.imperial: ("°F", "mph", "inHg", "mi"),
}


def _hourly_at(data: dict[str, Any], key: str, current_time: str) -> float | None:
    """Value of an hourly series at the hour containing current_time, or None."""
    hourly = data.get("hourly") or {}
    series = hourly.get(key) or []
    hour = str(current_time)[:13]  # "2026-10-28T14"
    for i, t in enumerate(hourly.get("time") or []):
        if str(t)[:13] == hour:
            return series[i] if i < len(series) else None
    return None


def _clock(value: Any) -> str | None:
    """'2026-10-28T05:42' -> '05:42'; missing values (polar day/night) -> None."""
    return str(value).split("T")[-1][:5] if value else None


def parse_forecast(data: dict[str, Any], units: Units, lat: float, lon: float) -> WeatherReport:
    """Normalize an Open-Meteo forecast response into our own schema."""
    try:
        cur, daily = data["current"], data["daily"]
        is_day = bool(cur.get("is_day", 1))
        text, icon = describe(int(cur["weather_code"]), is_day)
        direction = cur.get("wind_direction_10m")
        metric = units == Units.metric

        pressure = cur.get("pressure_msl")
        if pressure is not None:
            pressure = round(pressure) if metric else round(hpa_to_inhg(pressure), 2)

        vis_m = _hourly_at(data, "visibility", cur["time"])
        visibility = None if vis_m is None else round(m_to_km(vis_m) if metric else m_to_mi(vis_m), 1)

        uv = _hourly_at(data, "uv_index", cur["time"])
        uv = None if uv is None else round(uv, 1)
        current = CurrentConditions(
            temperature=round(cur["temperature_2m"]),
            feels_like=round(cur["apparent_temperature"]),
            humidity=round(cur["relative_humidity_2m"]),
            wind_speed=round(cur["wind_speed_10m"]),
            wind_direction=round(direction) if direction is not None else None,
            wind_compass=compass(direction) if direction is not None else None,
            pressure=pressure,
            visibility=visibility,
            uv_index=uv,
            uv_category=uv_category(uv) if uv is not None else None,
            description=text,
            icon=icon,
            is_day=is_day,
        )
        chances = daily.get("precipitation_probability_max") or []
        days = []
        for i, day in enumerate(daily["time"]):
            d_text, d_icon = describe(int(daily["weather_code"][i]))
            chance = chances[i] if i < len(chances) else None
            days.append(
                DailyForecast(
                    date=day,
                    high=round(daily["temperature_2m_max"][i]),
                    low=round(daily["temperature_2m_min"][i]),
                    precipitation_chance=None if chance is None else round(chance),
                    description=d_text,
                    icon=d_icon,
                )
            )
        temp_unit, wind_unit, pressure_unit, visibility_unit = _LABELS[units]
        sunrises, sunsets = daily.get("sunrise") or [], daily.get("sunset") or []
        uv_maxes = daily.get("uv_index_max") or []
        uv_max = uv_maxes[0] if uv_maxes else None
        return WeatherReport(
            latitude=lat,
            longitude=lon,
            timezone=data.get("timezone"),
            units=units,
            temp_unit=temp_unit,
            wind_unit=wind_unit,
            pressure_unit=pressure_unit,
            visibility_unit=visibility_unit,
            sunrise=_clock(sunrises[0]) if sunrises else None,
            sunset=_clock(sunsets[0]) if sunsets else None,
            uv_max=None if uv_max is None else round(uv_max, 1),
            observed_time=str(cur["time"]).split("T")[-1][:5],
            current=current,
            daily=days,
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:  # pydantic errors are ValueErrors
        raise UpstreamError("Weather data came back in an unexpected format.") from exc


class WeatherService:
    def __init__(self, client: httpx.AsyncClient, cache: AsyncTTLCache, url: str) -> None:
        self._client = client
        self._cache = cache
        self._url = url

    async def get_report(self, lat: float, lon: float, units: Units) -> WeatherReport:
        lat, lon = round(lat, 2), round(lon, 2)  # ~1 km; also makes cache keys reusable

        async def fetch() -> WeatherReport:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": _CURRENT,
                "daily": _DAILY,
                "hourly": _HOURLY,
                "timezone": "auto",
                "forecast_days": 7,
                **_UNIT_PARAMS[units],
            }
            try:
                resp = await self._client.get(self._url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise UpstreamError("Weather data is unavailable. Try again in a moment.") from exc
            return parse_forecast(data, units, lat, lon)

        return await self._cache.get_or_set(("wx", lat, lon, units.value), fetch)

from typing import Any

import httpx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import CurrentConditions, DailyForecast, Units, WeatherReport
from app.services.wmo import compass, describe

_CURRENT = "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m,wind_direction_10m"
_DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"

_UNIT_PARAMS = {
    Units.metric: {"temperature_unit": "celsius", "wind_speed_unit": "kmh"},
    Units.imperial: {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph"},
}
_LABELS = {Units.metric: ("°C", "km/h"), Units.imperial: ("°F", "mph")}


def parse_forecast(data: dict[str, Any], units: Units, lat: float, lon: float) -> WeatherReport:
    """Normalize an Open-Meteo forecast response into our own schema."""
    try:
        cur, daily = data["current"], data["daily"]
        is_day = bool(cur.get("is_day", 1))
        text, icon = describe(int(cur["weather_code"]), is_day)
        direction = cur.get("wind_direction_10m")
        current = CurrentConditions(
            temperature=round(cur["temperature_2m"]),
            feels_like=round(cur["apparent_temperature"]),
            humidity=round(cur["relative_humidity_2m"]),
            wind_speed=round(cur["wind_speed_10m"]),
            wind_compass=compass(direction) if direction is not None else None,
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
        temp_unit, wind_unit = _LABELS[units]
        return WeatherReport(
            latitude=lat,
            longitude=lon,
            timezone=data.get("timezone"),
            units=units,
            temp_unit=temp_unit,
            wind_unit=wind_unit,
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

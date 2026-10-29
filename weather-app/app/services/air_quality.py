from typing import Any

import httpx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import AirQuality
from app.services.scales import aqi_category


def _round1(value: Any) -> float | None:
    return None if value is None else round(float(value), 1)


def parse_air_quality(data: dict[str, Any]) -> AirQuality:
    """Normalize an Open-Meteo air-quality response (US AQI)."""
    try:
        cur = data["current"]
        raw = cur["us_aqi"]
        if raw is None:  # no coverage or no reading for this spot
            raise ValueError("no AQI value")
        aqi = round(raw)
        category, level, advice = aqi_category(aqi)
        return AirQuality(
            aqi=aqi,
            category=category,
            level=level,
            advice=advice,
            meter_percent=round(min(max(aqi, 0), 500) / 5, 1),
            pm2_5=_round1(cur.get("pm2_5")),
            pm10=_round1(cur.get("pm10")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise UpstreamError("Air quality data is unavailable for this location.") from exc


class AirQualityService:
    def __init__(self, client: httpx.AsyncClient, cache: AsyncTTLCache, url: str) -> None:
        self._client = client
        self._cache = cache
        self._url = url

    async def get(self, lat: float, lon: float) -> AirQuality:
        async def fetch() -> AirQuality:
            params = {"latitude": lat, "longitude": lon, "current": "us_aqi,pm10,pm2_5", "timezone": "auto"}
            try:
                resp = await self._client.get(self._url, params=params)
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise UpstreamError("Air quality is unavailable right now.") from exc
            return parse_air_quality(data)

        return await self._cache.get_or_set(("aq", lat, lon), fetch)

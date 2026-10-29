from typing import Any, Protocol

import httpx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.models import Location
from app.services.ranking import parse_query, rank


class GeocodingProvider(Protocol):
    """Anything that can turn free text into candidate locations."""

    async def suggest(self, query: str, limit: int = 8) -> list[Location]: ...


class OpenMeteoGeocoder:
    """Open-Meteo geocoding. It matches on place name only, so we search on the
    first comma-separated part and use the rest (state, country) to rank."""

    def __init__(self, client: httpx.AsyncClient, cache: AsyncTTLCache, url: str) -> None:
        self._client = client
        self._cache = cache
        self._url = url

    async def _search(self, name: str) -> list[dict[str, Any]]:
        async def fetch() -> list[dict[str, Any]]:
            try:
                resp = await self._client.get(
                    self._url, params={"name": name, "count": 20, "language": "en", "format": "json"}
                )
                resp.raise_for_status()
                return resp.json().get("results") or []  # key is absent when nothing matches
            except (httpx.HTTPError, ValueError, AttributeError) as exc:
                raise UpstreamError("Place search is unavailable. Try again in a moment.") from exc

        return await self._cache.get_or_set(("geo", name.casefold()), fetch)

    async def suggest(self, query: str, limit: int = 8) -> list[Location]:
        head, rest = parse_query(query)
        if len(head) < 2:
            return []

        raw = await self._search(head)
        if not raw and "," not in query and " " in head:
            # "Patna Bihar" without a comma: retry on the first word, rank on the rest.
            words = head.split()
            head, rest = words[0], words[1:]
            raw = await self._search(head)

        locations: list[Location] = []
        seen: set[str] = set()
        for r in rank(raw, head, rest):
            try:
                loc = Location(
                    name=r["name"],
                    admin1=r.get("admin1"),
                    country=r.get("country") or r.get("country_code") or "",
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    timezone=r.get("timezone"),
                    population=r.get("population"),
                )
            except (KeyError, ValueError):
                continue  # skip malformed entries
            if loc.label in seen:
                continue
            seen.add(loc.label)
            locations.append(loc)
            if len(locations) >= limit:
                break
        return locations

import asyncio

import httpx
import pytest
import respx

from app.cache import AsyncTTLCache
from app.errors import UpstreamError
from app.services.geocoding import OpenMeteoGeocoder
from tests.conftest import GEO_URL, PARIS


def run_suggest(*queries, limit=8):
    """Run queries against one geocoder instance and return the list of results."""

    async def go():
        async with httpx.AsyncClient() as client:
            geo = OpenMeteoGeocoder(client, AsyncTTLCache(10, 60), GEO_URL)
            return [await geo.suggest(q, limit) for q in queries]

    return asyncio.run(go())


def test_state_context_filters_results():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).respond(json=PARIS)
        (result,) = run_suggest("Paris, Texas")
    assert [loc.label for loc in result] == ["Paris, Texas, United States"]


def test_request_uses_first_part_of_query():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(GEO_URL).respond(json=PARIS)
        run_suggest("Paris, Texas, United States")
    assert route.calls.last.request.url.params["name"] == "Paris"


def test_limit_and_population_order():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).respond(json=PARIS)
        (result,) = run_suggest("Paris", limit=2)
    assert [loc.admin1 for loc in result] == ["Île-de-France", "Texas"]


def test_missing_results_key_means_no_matches():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).respond(json={"generationtime_ms": 0.5})
        (result,) = run_suggest("Zzzzzz")
    assert result == []


def test_short_query_makes_no_request():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(GEO_URL).respond(json=PARIS)
        (result,) = run_suggest("p")
    assert result == [] and route.call_count == 0


def test_multiword_without_comma_falls_back_to_first_word():
    def handler(request):
        if request.url.params["name"] == "Paris Texas":
            return httpx.Response(200, json={})
        return httpx.Response(200, json=PARIS)

    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).mock(side_effect=handler)
        (result,) = run_suggest("Paris Texas")
    assert [loc.admin1 for loc in result] == ["Texas"]


def test_upstream_failure_raises_upstream_error():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).respond(500)
        with pytest.raises(UpstreamError):
            run_suggest("Paris")


def test_network_error_raises_upstream_error():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(GEO_URL).mock(side_effect=httpx.ConnectTimeout("slow"))
        with pytest.raises(UpstreamError):
            run_suggest("Paris")


def test_repeat_query_is_served_from_cache():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(GEO_URL).respond(json=PARIS)
        run_suggest("Paris", "paris, texas")  # same cache key: "paris"
    assert route.call_count == 1

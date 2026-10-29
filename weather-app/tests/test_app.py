from tests.conftest import FORECAST_URL, GEO_URL  # noqa: F401


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_index_has_search_box(client):
    r = client.get("/")
    assert r.status_code == 200 and 'hx-get="/partials/suggest"' in r.text


def test_suggest_below_min_chars_is_empty(client, api):
    r = client.get("/partials/suggest", params={"q": "p"})
    assert r.status_code == 200 and "<li" not in r.text
    assert api.geo.call_count == 0


def test_suggest_renders_ranked_options(client):
    r = client.get("/partials/suggest", params={"q": "Paris, Texas"})
    assert "Texas, United States" in r.text and "Île-de-France" not in r.text
    assert "/partials/weather?lat=33.66" in r.text


def test_suggest_no_match(client, api):
    api.geo.respond(json={})
    assert "No places match" in client.get("/partials/suggest", params={"q": "zzzz"}).text


def test_suggest_upstream_error_shows_message(client, api):
    api.geo.respond(500)
    r = client.get("/partials/suggest", params={"q": "Paris"})
    assert r.status_code == 200 and "Place search is unavailable" in r.text


def test_weather_partial_renders_report(client):
    r = client.get("/partials/weather", params={"lat": 25.59, "lon": 85.14, "name": "Patna, Bihar, India"})
    assert r.status_code == 200
    text = r.text
    assert "Patna, Bihar, India" in text and "31°C" in text and "Partly cloudy" in text
    assert "Today" in text and "55% rain" in text
    assert 'aria-pressed="true"' in text and "units=imperial" in text


def test_weather_partial_units_toggle_is_forwarded(client, api):
    client.get("/partials/weather", params={"lat": 1, "lon": 2, "units": "imperial"})
    assert api.forecast.calls.last.request.url.params["temperature_unit"] == "fahrenheit"


def test_weather_partial_upstream_error(client, api):
    api.forecast.respond(500)
    r = client.get("/partials/weather", params={"lat": 1, "lon": 2, "name": "X"})
    assert r.status_code == 200 and "Weather data is unavailable" in r.text and "Try again" in r.text


def test_weather_partial_escapes_name(client):
    r = client.get("/partials/weather", params={"lat": 1, "lon": 2, "name": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in r.text


def test_api_weather_json(client):
    data = client.get("/api/weather", params={"lat": 25.59, "lon": 85.14}).json()
    assert data["current"]["temperature"] == 31 and len(data["daily"]) == 3


def test_api_weather_upstream_error_is_502(client, api):
    api.forecast.respond(500)
    r = client.get("/api/weather", params={"lat": 1, "lon": 2})
    assert r.status_code == 502 and "detail" in r.json()


def test_api_suggest_json(client):
    r = client.get("/api/locations/suggest", params={"q": "Paris"})
    assert r.json()[0]["admin1"] == "Île-de-France"


def test_coordinates_and_units_are_validated(client):
    assert client.get("/api/weather", params={"lat": 999, "lon": 0}).status_code == 422
    assert client.get("/partials/weather", params={"lat": 1, "lon": 2, "units": "kelvin"}).status_code == 422


def test_index_wires_up_combobox(client):
    html = client.get("/").text
    assert "js/combobox.js" in html
    assert 'role="combobox"' in html and 'aria-controls="suggestion-list"' in html
    assert 'id="combo-status"' in html
    assert 'hx-trigger="input changed delay:300ms"' in html  # no "search" event


def test_combobox_script_is_served(client):
    r = client.get("/static/js/combobox.js")
    assert r.status_code == 200 and "aria-activedescendant" in r.text


def test_suggestion_options_have_combobox_markup(client):
    html = client.get("/partials/suggest", params={"q": "Paris"}).text
    assert 'id="suggestion-list"' in html
    assert 'id="opt-0"' in html and 'id="opt-1"' in html
    assert html.count('aria-selected="false"') == html.count('role="option"') == 3
    assert 'data-label="Paris, Île-de-France, France"' in html
    assert "tabindex" not in html and "hx-on" not in html

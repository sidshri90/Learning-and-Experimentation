# Weather App

FastAPI + HTMX + Jinja2. Autocomplete place search and weather from Open-Meteo (free, no API key).

## Run (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\fetch_htmx.py
copy .env.example .env
uvicorn app.main:app --reload
```

If activation is blocked, run once in that window:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

## Run (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_htmx.py
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs

## Test

```
pytest
```

Tests mock Open-Meteo with respx, so they run offline.

## Manual check: search box keyboard behaviour

JavaScript behaviour isn't covered by pytest, so verify by hand after changes to `combobox.js`:

1. Type `par`. The list opens. Nothing is highlighted yet.
2. Press Down. The first option highlights. Press Up from the first option to wrap to the last.
3. Press Enter with an option highlighted. The box fills with its full name, the list closes, weather loads.
4. Type `par` again and press Enter with nothing highlighted. The first suggestion is chosen.
5. Type `par`, then press Esc. The list closes and the text stays. Press Esc again to clear the text.
6. Type `par`, then click elsewhere on the page. The list closes.
7. Type `par`, then press Tab. The list closes and focus moves on.
8. Click a suggestion with the mouse. It works the same as Enter.

## Manual check: location button and recent searches

1. Click **Use my location**. Your browser asks for permission. Allow it: the weather loads for
   "Your location (lat, lon)". (Works on `localhost` and on HTTPS sites only.)
2. Click it again and choose Block in the browser prompt (or block it in site settings). A clear message appears.
3. Pick three different cities. Chips appear under the search box, newest first. Pick six: only five stay.
4. Click a chip. The weather loads and the chip moves to the front.
5. Click **Clear**. The chips disappear. Reload the page: they stay gone.
6. Pick a city, switch to °F, then search another city. It should stay in °F. Reload: still °F.

## Optional: JavaScript checks (needs Node.js)

```
node tests/js/combobox.test.js
node tests/js/geolocate.test.js
node tests/js/memory.test.js
```

These run the browser scripts against a small fake DOM. They are not a replacement for the manual checks above.

## Status

Milestone 6: "Use my location" button, last 5 searches, and a remembered °C/°F choice, on top of the
24-hour strip, US AQI, live place search, 7-day forecast, detail tiles, caching, a loading state and a
keyboard-accessible search box.
Next: hardening (rate limiting, security headers), Dockerfile, deployment guide.

## Data sources

Weather: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0, non-commercial free tier).
Air quality: Copernicus Atmosphere Monitoring Service, via Open-Meteo.

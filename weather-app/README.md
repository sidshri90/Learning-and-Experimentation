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

## Status

Milestone 5: 24-hour strip with sunrise/sunset markers and US AQI (air quality), on top of live place search,
7-day forecast, detail tiles, °C/°F toggle, caching, a loading state, and a keyboard-accessible search box.
Next: "use my location" button, then hardening and deployment.

## Data sources

Weather: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0, non-commercial free tier).
Air quality: Copernicus Atmosphere Monitoring Service, via Open-Meteo.

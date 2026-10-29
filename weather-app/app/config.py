from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from WEATHER_* environment variables or a .env file."""

    model_config = SettingsConfigDict(env_prefix="WEATHER_", env_file=".env", extra="ignore")

    app_name: str = "Weather"
    debug: bool = False

    # Autocomplete
    suggest_min_chars: int = 2
    suggest_debounce_ms: int = 300
    suggest_limit: int = 8

    # Upstream APIs (Open-Meteo, no key needed)
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    http_timeout: float = 8.0

    # Caching (seconds)
    geocode_cache_ttl: int = 3600
    forecast_cache_ttl: int = 600
    cache_maxsize: int = 512


@lru_cache
def get_settings() -> Settings:
    return Settings()

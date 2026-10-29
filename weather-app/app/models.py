import datetime as dt
from enum import Enum

from pydantic import BaseModel


class Units(str, Enum):
    metric = "metric"  # °C, km/h
    imperial = "imperial"  # °F, mph


class Location(BaseModel):
    name: str
    admin1: str | None = None  # state / region
    country: str = ""
    latitude: float
    longitude: float
    timezone: str | None = None
    population: int | None = None

    @property
    def label(self) -> str:
        """Disambiguated name, e.g. 'Patna, Bihar, India'."""
        parts = [self.name]
        if self.admin1 and self.admin1.casefold() != self.name.casefold():
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class CurrentConditions(BaseModel):
    temperature: int
    feels_like: int
    humidity: int
    wind_speed: int
    wind_direction: int | None = None  # degrees the wind blows FROM
    wind_compass: str | None = None
    pressure: float | None = None  # hPa (metric) or inHg (imperial)
    visibility: float | None = None  # km (metric) or miles (imperial)
    uv_index: float | None = None
    uv_category: str | None = None
    description: str
    icon: str
    is_day: bool


class DailyForecast(BaseModel):
    date: dt.date
    high: int
    low: int
    precipitation_chance: int | None = None
    description: str
    icon: str


class WeatherReport(BaseModel):
    latitude: float
    longitude: float
    timezone: str | None = None
    units: Units
    temp_unit: str  # "°C" or "°F"
    wind_unit: str  # "km/h" or "mph"
    pressure_unit: str  # "hPa" or "inHg"
    visibility_unit: str  # "km" or "mi"
    observed_time: str  # local time at the location, "HH:MM"
    sunrise: str | None = None  # today, local "HH:MM"
    sunset: str | None = None
    uv_max: float | None = None  # today's peak UV index
    current: CurrentConditions
    daily: list[DailyForecast]

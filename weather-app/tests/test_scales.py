import pytest

from app.services.scales import aqi_category, hpa_to_inhg, m_to_km, m_to_mi, uv_category


def test_conversions():
    assert m_to_km(10000) == 10
    assert round(m_to_mi(10000), 2) == 6.21
    assert round(hpa_to_inhg(1013.25), 2) == 29.92


@pytest.mark.parametrize(
    "uv, label",
    [(0, "Low"), (2.9, "Low"), (3, "Moderate"), (5.9, "Moderate"), (6, "High"),
     (7.9, "High"), (8, "Very high"), (10.9, "Very high"), (11, "Extreme"), (14, "Extreme")],
)
def test_uv_category(uv, label):
    assert uv_category(uv) == label


@pytest.mark.parametrize(
    "aqi, label, level",
    [(0, "Good", "good"), (50, "Good", "good"), (51, "Moderate", "moderate"), (100, "Moderate", "moderate"),
     (101, "Unhealthy for sensitive groups", "sensitive"), (150, "Unhealthy for sensitive groups", "sensitive"),
     (151, "Unhealthy", "unhealthy"), (200, "Unhealthy", "unhealthy"), (201, "Very unhealthy", "very"),
     (300, "Very unhealthy", "very"), (301, "Hazardous", "hazardous"), (500, "Hazardous", "hazardous")],
)
def test_aqi_category(aqi, label, level):
    assert aqi_category(aqi)[:2] == (label, level)

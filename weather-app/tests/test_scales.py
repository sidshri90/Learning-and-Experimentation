import pytest

from app.services.scales import hpa_to_inhg, m_to_km, m_to_mi, uv_category


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

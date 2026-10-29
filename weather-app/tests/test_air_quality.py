import pytest

from app.errors import UpstreamError
from app.services.air_quality import parse_air_quality
from tests.conftest import aq_payload


def test_parse_air_quality():
    aq = parse_air_quality(aq_payload(us_aqi=161.6))
    assert (aq.aqi, aq.category, aq.level) == (162, "Unhealthy", "unhealthy")
    assert aq.pm2_5 == 61.2 and aq.pm10 == 88.3
    assert aq.meter_percent == 32.4  # 162 on a 0-500 scale


def test_meter_is_clamped():
    assert parse_air_quality(aq_payload(us_aqi=640)).meter_percent == 100.0
    assert parse_air_quality(aq_payload(us_aqi=0)).meter_percent == 0.0


def test_pm_values_are_optional():
    aq = parse_air_quality({"current": {"us_aqi": 40}})
    assert aq.pm2_5 is None and aq.pm10 is None and aq.category == "Good"


@pytest.mark.parametrize("payload", [{}, {"current": {}}, {"current": {"us_aqi": None}}, {"current": {"us_aqi": "x"}}])
def test_bad_payloads_raise_upstream_error(payload):
    with pytest.raises(UpstreamError):
        parse_air_quality(payload)

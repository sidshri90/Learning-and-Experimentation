"""Unit conversions and category labels for weather readings (pure functions)."""

_HPA_TO_INHG = 0.029529983071445
_M_PER_MILE = 1609.344


def hpa_to_inhg(hpa: float) -> float:
    return hpa * _HPA_TO_INHG


def m_to_km(meters: float) -> float:
    return meters / 1000


def m_to_mi(meters: float) -> float:
    return meters / _M_PER_MILE


def uv_category(uv: float) -> str:
    """WHO UV index bands."""
    if uv < 3:
        return "Low"
    if uv < 6:
        return "Moderate"
    if uv < 8:
        return "High"
    if uv < 11:
        return "Very high"
    return "Extreme"


def aqi_category(aqi: float) -> tuple[str, str, str]:
    """US AQI -> (label, css level, one-line general guidance)."""
    if aqi <= 50:
        return "Good", "good", "Air quality is satisfactory."
    if aqi <= 100:
        return "Moderate", "moderate", "Acceptable. Unusually sensitive people may notice effects."
    if aqi <= 150:
        return ("Unhealthy for sensitive groups", "sensitive",
                "Sensitive groups should limit prolonged outdoor exertion.")
    if aqi <= 200:
        return "Unhealthy", "unhealthy", "Everyone may begin to experience health effects."
    if aqi <= 300:
        return "Very unhealthy", "very", "Health alert: everyone may experience more serious effects."
    return "Hazardous", "hazardous", "Emergency conditions. Avoid outdoor exertion."

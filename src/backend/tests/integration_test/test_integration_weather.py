"""Integration: weather route delegates to weather_service (FR-06)."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import weather_app


def test_get_weather_now_returns_service_payload():
    app = weather_app()
    with TestClient(app) as client:
        with patch("app.api.v1.weather.weather_service.fetch_weather_now") as m:
            m.return_value = {"location": "Test", "temp": "20°C"}
            r = client.get("/api/weather/now", params={"lat": 29.87, "lon": 121.54})
    assert r.status_code == 200
    assert r.json()["temp"] == "20°C"
    m.assert_called_once()

"""weather_service._wind_scale_to_desc (pure helper)."""
import app.services.weather_service as weather_service


def test_wind_scale_light_breeze():
    assert weather_service._wind_scale_to_desc("0") == "Light Breeze"
    assert weather_service._wind_scale_to_desc("2") == "Light Breeze"


def test_wind_scale_moderate_and_strong():
    assert weather_service._wind_scale_to_desc("3") == "Moderate Breeze"
    assert weather_service._wind_scale_to_desc("6") == "Strong Breeze"


def test_wind_scale_storm_and_invalid():
    assert weather_service._wind_scale_to_desc("12") == "Storm"
    assert weather_service._wind_scale_to_desc("notint") == "—"
    assert weather_service._wind_scale_to_desc("") == "Light Breeze"

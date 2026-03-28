"""Unit: Pydantic schemas used at API boundaries (FR-01, FR-05 partial, FR-06)."""
import pytest
from pydantic import ValidationError

from app.schemas.ai import ChatReq
from app.schemas.auth import UserLogin
from app.schemas.user import UserCreate
from app.schemas.weather import WeatherLatLonParams


def test_user_create_password_mismatch():
    with pytest.raises(ValidationError):
        UserCreate(
            username="abc",
            password="secret1",
            confirm_password="secret2",
        )


def test_user_create_username_invalid_char():
    with pytest.raises(ValidationError):
        UserCreate(
            username="ab!",
            password="secret1",
            confirm_password="secret1",
        )


def test_user_login_empty_username():
    with pytest.raises(ValidationError):
        UserLogin(username="   ", password="x")


def test_weather_lat_lon_coerces_numeric_string():
    m = WeatherLatLonParams.model_validate({"lat": "29.5", "lon": "121.0"})
    assert m.lat == 29.5
    assert m.lon == 121.0


def test_chat_req_accepts_history_default():
    r = ChatReq(query="hello")
    assert r.query == "hello"
    assert r.history == []


def test_chat_req_accepts_history_entries():
    r = ChatReq(query="q", history=[{"role": "user", "content": "hi"}])
    assert len(r.history) == 1

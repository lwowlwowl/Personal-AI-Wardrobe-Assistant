"""Integration: auth HTTP routes with mocked DB and crud (FR-01)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from .minimal_apps import auth_app_with_mock_db


@pytest.fixture
def auth_client():
    app, _ = auth_app_with_mock_db()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_register_success_returns_user_payload(auth_client):
    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.username = "newuser"
    mock_user.email = "n@example.com"
    mock_user.is_active = True
    mock_user.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with patch("app.api.v1.auth.crud.create_user", return_value=(mock_user, None)):
        r = auth_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "n@example.com",
                "password": "secret12",
                "confirm_password": "secret12",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["username"] == "newuser"
    assert body["data"]["id"] == 42


def test_register_conflict_returns_409(auth_client):
    with patch(
        "app.api.v1.auth.crud.create_user",
        return_value=(None, "That username is already registered."),
    ):
        r = auth_client.post(
            "/api/auth/register",
            json={
                "username": "taken",
                "password": "secret12",
                "confirm_password": "secret12",
            },
        )
    assert r.status_code == 409
    assert r.json()["success"] is False


def test_login_success_returns_token(auth_client):
    mock_user = MagicMock()
    mock_user.id = 7
    mock_user.username = "alice"
    mock_user.email = "a@example.com"
    mock_user.is_active = True

    with patch("app.api.v1.auth.crud.authenticate_user", return_value=(mock_user, None)):
        with patch("app.api.v1.auth.crud.create_access_token", return_value="tok.test"):
            r = auth_client.post(
                "/api/auth/login",
                json={"username": "alice", "password": "x", "remember": False},
            )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["access_token"] == "tok.test"
    assert data["user_id"] == 7


def test_login_invalid_credentials_returns_401_payload(auth_client):
    with patch(
        "app.api.v1.auth.crud.authenticate_user",
        return_value=(None, "Incorrect username or password."),
    ):
        r = auth_client.post(
            "/api/auth/login",
            json={"username": "no", "password": "bad", "remember": False},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["status_code"] == 401


def test_verify_token_success(auth_client):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "u"
    mock_user.email = "e@e.com"
    mock_user.is_active = True
    mock_user.created_at = datetime(2026, 3, 1, tzinfo=timezone.utc)

    with patch("app.api.v1.auth.crud.verify_access_token", return_value={"sub": "u", "user_id": 1}):
        with patch("app.api.v1.auth.crud.get_user_by_id", return_value=mock_user):
            r = auth_client.get("/api/auth/verify", params={"token": "any"})
    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["username"] == "u"


def test_verify_token_invalid(auth_client):
    with patch("app.api.v1.auth.crud.verify_access_token", return_value=None):
        r = auth_client.get("/api/auth/verify", params={"token": "bad"})
    assert r.status_code == 401

"""Integration: POST /api/auth/reset-password-by-identity (FR-01 account recovery)."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import auth_app_with_mock_db


def test_reset_password_by_identity_success():
    app, _ = auth_app_with_mock_db()
    try:
        user = SimpleNamespace(
            username="alice",
            email="alice@example.com",
            is_active=True,
        )
        with patch("app.api.v1.auth.crud.get_user_by_username", return_value=user):
            with patch(
                "app.api.v1.auth.crud.update_user_password",
                return_value=(True, None),
            ):
                with TestClient(app) as client:
                    r = client.post(
                        "/api/auth/reset-password-by-identity",
                        json={
                            "email": "alice@example.com",
                            "username": "alice",
                            "new_password": "newsecret1",
                            "confirm_password": "newsecret1",
                        },
                    )
        assert r.status_code == 200
        assert r.json().get("success") is True
    finally:
        app.dependency_overrides.clear()


def test_reset_password_by_identity_email_mismatch():
    app, _ = auth_app_with_mock_db()
    try:
        user = SimpleNamespace(
            username="alice",
            email="other@example.com",
            is_active=True,
        )
        with patch("app.api.v1.auth.crud.get_user_by_username", return_value=user):
            with TestClient(app) as client:
                r = client.post(
                    "/api/auth/reset-password-by-identity",
                    json={
                        "email": "alice@example.com",
                        "username": "alice",
                        "new_password": "newsecret1",
                        "confirm_password": "newsecret1",
                    },
                )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()

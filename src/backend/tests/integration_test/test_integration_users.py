"""Integration: /api/users/me with mocked auth + DB (FR-01, FR-04)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from .minimal_apps import users_app_with_mock_db


def _user_ns(**kwargs):
    defaults = dict(
        id=1,
        username="u",
        email=None,
        full_name=None,
        avatar_url=None,
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_read_users_me_success():
    app, _ = users_app_with_mock_db()
    try:
        mock_user = _user_ns(
            id=5,
            username="me",
            email="m@e.com",
            full_name="Me User",
        )

        with patch("app.api.v1.users.crud.verify_access_token", return_value={"user_id": 5, "sub": "me"}):
            with patch("app.api.v1.users.crud.get_user_by_id", return_value=mock_user):
                with TestClient(app) as client:
                    r = client.get("/api/users/me", params={"token": "t"})
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "me"
        assert data["id"] == 5
    finally:
        app.dependency_overrides.clear()


def test_patch_users_me_updates_via_crud():
    app, _ = users_app_with_mock_db()
    try:
        current = MagicMock()
        current.id = 3
        updated = _user_ns(
            id=3,
            username="newname",
            email="e@e.com",
        )

        with patch("app.api.v1.users.get_current_user", return_value=current):
            with patch("app.api.v1.users.crud.update_user", return_value=updated):
                with TestClient(app) as client:
                    r = client.patch(
                        "/api/users/me",
                        params={"token": "tok"},
                        json={"full_name": "Hello"},
                    )
        assert r.status_code == 200
        assert r.json()["username"] == "newname"
    finally:
        app.dependency_overrides.clear()

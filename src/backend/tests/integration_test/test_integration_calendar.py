"""Integration: GET /api/calendar/outfits (wardrobe / outfit history surface, FR-13 adjacency)."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import calendar_app_with_mock_db


def test_get_calendar_outfits_empty_month():
    app, db_mock = calendar_app_with_mock_db()
    try:
        user = SimpleNamespace(id=11, username="cal")
        q = db_mock.query.return_value
        q.join.return_value.filter.return_value.all.return_value = []

        with patch("app.api.v1.calendar.get_current_user", return_value=user):
            with TestClient(app) as client:
                r = client.get(
                    "/api/calendar/outfits",
                    params={"token": "t", "year": 2026, "month": 3},
                )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["outfits"] == {}
        assert body["data"]["monthStats"]["daysRecorded"] == 0
        assert body["data"]["monthStats"]["uniqueItems"] == 0
    finally:
        app.dependency_overrides.clear()

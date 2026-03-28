"""Integration: /api/analysis/total-items/summary (wardrobe insights, FR-13 adjacency)."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import analysis_app_with_mock_db


def test_get_total_items_summary_success():
    app, _ = analysis_app_with_mock_db()
    try:
        user = SimpleNamespace(id=4, username="a")
        payload = {"ok": True, "total": 12}

        with patch("app.api.v1.analysis.get_current_user", return_value=user):
            with patch(
                "app.api.v1.analysis.run_total_items_summary",
                return_value=payload,
            ):
                with TestClient(app) as client:
                    r = client.get(
                        "/api/analysis/total-items/summary",
                        params={"token": "t"},
                    )
        assert r.status_code == 200
        assert r.json() == payload
    finally:
        app.dependency_overrides.clear()

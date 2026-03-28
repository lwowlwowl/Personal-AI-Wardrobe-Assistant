"""Integration: GET /api/clothing list + filters (FR-13 search / filter)."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import clothing_app_with_mock_db


def test_clothing_list_success_empty():
    app, _ = clothing_app_with_mock_db()
    try:
        user = SimpleNamespace(id=2, username="c")

        with patch("app.api.v1.clothing.get_current_user", return_value=user):
            with patch(
                "app.api.v1.clothing.crud.clothing_crud.get_clothing_items",
                return_value=([], 0),
            ):
                with TestClient(app) as client:
                    r = client.get("/api/clothing", params={"token": "t", "page": 1})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["pagination"]["total"] == 0
        assert data["data"]["pagination"]["total_pages"] == 0
    finally:
        app.dependency_overrides.clear()


def test_clothing_list_passes_search_to_crud():
    app, _ = clothing_app_with_mock_db()
    try:
        user = SimpleNamespace(id=2, username="c")

        with patch("app.api.v1.clothing.get_current_user", return_value=user):
            with patch(
                "app.api.v1.clothing.crud.clothing_crud.get_clothing_items",
                return_value=([], 0),
            ) as m_get:
                with TestClient(app) as client:
                    r = client.get(
                        "/api/clothing",
                        params={
                            "token": "t",
                            "search": "blue jacket",
                            "category": "TOP",
                            "season": "winter",
                        },
                    )
        assert r.status_code == 200
        _, kwargs = m_get.call_args
        assert kwargs["search"] == "blue jacket"
        assert kwargs["category"] == "TOP"
        assert kwargs["season"] == "winter"
    finally:
        app.dependency_overrides.clear()

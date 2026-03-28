"""Integration: AI conversation CRUD (FR-05 / FR-08 persistence)."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import ai_chat_app_with_mock_db


def _user():
    return SimpleNamespace(id=7, username="u")


def _conv(**kwargs):
    defaults = dict(
        id=1,
        title="t",
        messages=[],
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_list_ai_conversations_success():
    app, _ = ai_chat_app_with_mock_db()
    try:
        with patch("app.api.v1.ai_chat.get_current_user", return_value=_user()):
            with patch(
                "app.api.v1.ai_chat.crud.ai_conversation_crud.list_by_user",
                return_value=([_conv(id=2, title="A")], 1, None),
            ):
                with TestClient(app) as client:
                    r = client.get("/api/ai/conversations", params={"token": "t"})
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["total"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["id"] == 2
        assert body["data"][0]["title"] == "A"
    finally:
        app.dependency_overrides.clear()


def test_create_ai_conversation_success():
    app, _ = ai_chat_app_with_mock_db()
    try:
        created = _conv(id=9, title="New")
        with patch("app.api.v1.ai_chat.get_current_user", return_value=_user()):
            with patch(
                "app.api.v1.ai_chat.crud.ai_conversation_crud.create",
                return_value=(created, None),
            ):
                with TestClient(app) as client:
                    r = client.post(
                        "/api/ai/conversations",
                        params={"token": "t"},
                        json={"title": "New", "messages": []},
                    )
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert r.json()["data"]["id"] == 9
    finally:
        app.dependency_overrides.clear()


def test_delete_ai_conversation_success():
    app, _ = ai_chat_app_with_mock_db()
    try:
        with patch("app.api.v1.ai_chat.get_current_user", return_value=_user()):
            with patch(
                "app.api.v1.ai_chat.crud.ai_conversation_crud.delete",
                return_value=(True, None),
            ):
                with TestClient(app) as client:
                    r = client.delete("/api/ai/conversations/5", params={"token": "t"})
        assert r.status_code == 200
        assert r.json()["success"] is True
    finally:
        app.dependency_overrides.clear()

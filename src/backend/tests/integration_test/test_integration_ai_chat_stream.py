"""Integration: POST /api/ai/chat/stream (FR-05 / FR-08 streaming path)."""
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import ai_chat_app_with_mock_db


def test_ai_chat_stream_rejects_empty_message():
    app, _ = ai_chat_app_with_mock_db()
    try:
        with TestClient(app) as client:
            with client.stream(
                "POST",
                "/api/ai/chat/stream",
                json={"query": "   "},
            ) as r:
                assert r.status_code == 200
                raw = r.read().decode("utf-8")
        assert "error" in raw
        assert "empty" in raw.lower() or "Message" in raw
    finally:
        app.dependency_overrides.clear()


def test_ai_chat_stream_yields_delta_and_done():
    app, _ = ai_chat_app_with_mock_db()
    ra_mod = sys.modules["AIwardrobe.agent.react_agent"]

    async def execute_stream(self, query: str, lang: str = "en"):
        yield "Hello"

    try:
        with patch.object(ra_mod.ReactAgent, "execute_stream", execute_stream):
            with TestClient(app) as client:
                with client.stream(
                    "POST",
                    "/api/ai/chat/stream",
                    json={"query": "What to wear?"},
                ) as r:
                    assert r.status_code == 200
                    raw = r.read().decode("utf-8")
        assert "delta" in raw
        assert "final" in raw
        assert "done" in raw
    finally:
        app.dependency_overrides.clear()

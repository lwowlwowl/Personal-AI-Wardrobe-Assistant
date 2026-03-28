"""Integration: virtual try-on routes call service layer (FR-10, FR-11; FR-12 N/A on API)."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.services.virtual_tryon_service import JsonEnvelope, PngBytesResult
from .minimal_apps import virtual_tryon_app_with_mock_db


@pytest.fixture
def vto_client():
    app, _ = virtual_tryon_app_with_mock_db()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_generate_returns_png_when_service_succeeds(vto_client):
    with patch(
        "app.api.v1.virtual_tryon.run_generate_virtual_tryon",
        return_value=PngBytesResult(data=b"\x89PNG\r\n\x1a\n"),
    ):
        r = vto_client.post(
            "/api/virtual-try-on/generate",
            json={
                "person_image": "p.png",
                "clothing_image": "c.png",
                "model_type": "2509",
                "prompt": "",
            },
        )
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("image/png")


def test_generate_returns_json_envelope_on_error(vto_client):
    with patch(
        "app.api.v1.virtual_tryon.run_generate_virtual_tryon",
        return_value=JsonEnvelope(
            status_code=400,
            body={"success": False, "message": "bad input"},
        ),
    ):
        r = vto_client.post(
            "/api/virtual-try-on/generate",
            json={"person_image": "p.png", "clothing_image": "c.png"},
        )
    assert r.status_code == 400
    assert r.json()["success"] is False


def test_upload_image_returns_envelope():
    app, _ = virtual_tryon_app_with_mock_db()
    try:
        with TestClient(app) as client:
            async_mock = AsyncMock(
                return_value=JsonEnvelope(status_code=200, body={"success": True, "path": "/x"})
            )
            with patch(
                "app.api.v1.virtual_tryon.run_upload_virtual_tryon_image",
                async_mock,
            ):
                r = client.post(
                    "/api/virtual-try-on/upload-image",
                    data={"token": "t"},
                    files={"file": ("a.png", b"fake", "image/png")},
                )
        assert r.status_code == 200
        assert r.json().get("success") is True
    finally:
        app.dependency_overrides.clear()

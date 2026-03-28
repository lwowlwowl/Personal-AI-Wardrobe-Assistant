"""Integration: model photo upload (supports FR-10 try-on user base images)."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from .minimal_apps import model_photos_app_with_mock_db


def test_upload_model_photo_success():
    app, _ = model_photos_app_with_mock_db()
    try:
        user = SimpleNamespace(id=99, username="m")
        saved = {
            "id": 1,
            "photo_name": "Primary",
            "image_url": "/uploads/99/x.jpg",
            "is_primary": True,
        }

        with patch("app.api.v1.model_photos.get_current_user", return_value=user):
            with patch(
                "app.api.v1.model_photos.save_upload_file",
                return_value="/uploads/99/x.jpg",
            ):
                with patch(
                    "app.api.v1.model_photos.crud.model_photo_crud.create_model_photo",
                    return_value=(saved, None),
                ):
                    with TestClient(app) as client:
                        r = client.post(
                            "/api/model-photos/upload",
                            params={"token": "t"},
                            data={
                                "photo_name": "Primary",
                                "description": "",
                                "is_primary": "true",
                            },
                            files={"file": ("p.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")},
                        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["id"] == 1
    finally:
        app.dependency_overrides.clear()

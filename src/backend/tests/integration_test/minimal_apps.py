"""
Minimal FastAPI apps for integration tests (single router + mocked get_db).

Importing app.main runs create_all() against DATABASE_URL; these factories avoid that.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI

from app.core.database import get_db


def auth_app_with_mock_db():
    from app.api.v1.auth import router as auth_router

    app = FastAPI()
    app.include_router(auth_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def weather_app():
    from app.api.v1.weather import router as weather_router

    app = FastAPI()
    app.include_router(weather_router)
    return app


def virtual_tryon_app_with_mock_db():
    from app.api.v1.virtual_tryon import router as v_router

    app = FastAPI()
    app.include_router(v_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def users_app_with_mock_db():
    from app.api.v1.users import router as users_router

    app = FastAPI()
    app.include_router(users_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def clothing_app_with_mock_db():
    from app.api.v1.clothing import router as clothing_router

    app = FastAPI()
    app.include_router(clothing_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def ai_chat_app_with_mock_db():
    from app.api.v1.ai_chat import router as ai_router

    app = FastAPI()
    app.include_router(ai_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def calendar_app_with_mock_db():
    from app.api.v1.calendar import router as calendar_router

    app = FastAPI()
    app.include_router(calendar_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def analysis_app_with_mock_db():
    from app.api.v1.analysis import router as analysis_router

    app = FastAPI()
    app.include_router(analysis_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock


def model_photos_app_with_mock_db():
    from app.api.v1.model_photos import router as mp_router

    app = FastAPI()
    app.include_router(mp_router)
    db_mock = MagicMock()

    def _ov():
        yield db_mock

    app.dependency_overrides[get_db] = _ov
    return app, db_mock

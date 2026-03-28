"""FastAPI dependency get_current_user (app.api.deps), called with explicit args."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.api.deps import get_current_user


def test_get_current_user_returns_user_when_valid():
    user = MagicMock()
    user.is_active = True
    db = MagicMock()
    with patch("app.api.deps.crud.verify_access_token", return_value={"user_id": 9, "sub": "nine"}):
        with patch("app.api.deps.crud.get_user_by_id", return_value=user):
            out = get_current_user(token="valid.jwt", db=db)
    assert out is user


def test_get_current_user_401_when_token_invalid():
    with patch("app.api.deps.crud.verify_access_token", return_value=None):
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="bad", db=MagicMock())
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_401_when_missing_user_id_in_payload():
    with patch("app.api.deps.crud.verify_access_token", return_value={"sub": "only"}):
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="t", db=MagicMock())
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_404_when_user_missing():
    with patch("app.api.deps.crud.verify_access_token", return_value={"user_id": 1, "sub": "a"}):
        with patch("app.api.deps.crud.get_user_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                get_current_user(token="t", db=MagicMock())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_current_user_403_when_inactive():
    user = MagicMock()
    user.is_active = False
    with patch("app.api.deps.crud.verify_access_token", return_value={"user_id": 1, "sub": "a"}):
        with patch("app.api.deps.crud.get_user_by_id", return_value=user):
            with pytest.raises(HTTPException) as exc:
                get_current_user(token="t", db=MagicMock())
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

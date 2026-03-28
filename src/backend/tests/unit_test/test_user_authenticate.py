"""Login auth (app.crud.user.authenticate_user); Session mocked to avoid a real DB."""
from unittest.mock import MagicMock

import pytest

from app.core.security import hash_password
from app.crud.user import authenticate_user


@pytest.fixture
def mock_db():
    return MagicMock()


def test_authenticate_user_success(mock_db):
    user = MagicMock()
    user.hashed_password = hash_password("secret123")
    user.is_active = True
    mock_db.query.return_value.filter.return_value.first.return_value = user

    u, err = authenticate_user(mock_db, "alice", "secret123")
    assert u is user
    assert err is None


def test_authenticate_user_wrong_password(mock_db):
    user = MagicMock()
    user.hashed_password = hash_password("right")
    mock_db.query.return_value.filter.return_value.first.return_value = user

    u, err = authenticate_user(mock_db, "alice", "wrong")
    assert u is None
    assert err == "Incorrect username or password."


def test_authenticate_user_unknown_username(mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    u, err = authenticate_user(mock_db, "nobody", "x")
    assert u is None
    assert "Incorrect" in (err or "")

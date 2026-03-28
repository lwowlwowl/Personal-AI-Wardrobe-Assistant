"""JWT creation and verification (app.core.security)."""
from datetime import datetime, timedelta

import jwt

import app.core.security as security
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    verify_access_token,
    verify_password,
    verify_password_reset_token,
    hash_password,
)


def test_create_and_verify_roundtrip():
    token = create_access_token(
        {"sub": "alice", "user_id": 7},
        expires_delta=timedelta(minutes=30),
    )
    payload = verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"
    assert payload["user_id"] == 7
    assert "exp" in payload


def test_verify_rejects_malformed_token():
    assert verify_access_token("not.a.jwt") is None
    assert verify_access_token("") is None


def test_verify_rejects_wrong_signature():
    token = create_access_token({"sub": "bob", "user_id": 1})
    parts = token.split(".")
    assert len(parts) == 3
    tampered = f"{parts[0]}.{parts[1]}." + ("x" * 20)
    assert verify_access_token(tampered) is None


def test_verify_rejects_expired_token():
    token = create_access_token(
        {"sub": "exp", "user_id": 99},
        expires_delta=timedelta(seconds=-1),
    )
    assert verify_access_token(token) is None


def test_password_hash_and_verify():
    h = hash_password("MyP@ssw0rd")
    assert verify_password("MyP@ssw0rd", h) is True
    assert verify_password("wrong", h) is False


def test_password_reset_token_roundtrip():
    tok = create_password_reset_token("user@example.com")
    assert verify_password_reset_token(tok) == "user@example.com"


def test_password_reset_token_rejects_access_token():
    access = create_access_token({"sub": "u", "user_id": 1})
    assert verify_password_reset_token(access) is None


def test_password_reset_token_rejects_expired():
    payload = {
        "email": "x@y.com",
        "type": "reset",
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    expired = jwt.encode(payload, security.SECRET_KEY, algorithm=security.ALGORITHM)
    assert verify_password_reset_token(expired) is None

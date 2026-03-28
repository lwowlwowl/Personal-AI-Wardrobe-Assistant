"""Password reset-by-identity schema (app.schemas.auth)."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import PasswordResetByIdentity


def test_password_reset_identity_passwords_must_match():
    with pytest.raises(ValidationError):
        PasswordResetByIdentity(
            email="a@b.com",
            username="userone",
            new_password="secret12",
            confirm_password="other",
        )


def test_password_reset_identity_username_trimmed():
    m = PasswordResetByIdentity(
        email="a@b.com",
        username="  ab ",
        new_password="secret12",
        confirm_password="secret12",
    )
    assert m.username == "ab"

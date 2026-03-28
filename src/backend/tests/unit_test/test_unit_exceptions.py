"""Application errors (app.core.exceptions)."""
from app.core.exceptions import AppError


def test_app_error_fields():
    e = AppError("not allowed", status_code=403)
    assert e.message == "not allowed"
    assert e.status_code == 403
    assert str(e) == "not allowed"


def test_app_error_default_status():
    e = AppError("oops")
    assert e.status_code == 400

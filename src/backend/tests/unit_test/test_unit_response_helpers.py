"""Unified API JSON helpers (app.utils.response_helpers)."""
from app.utils.response_helpers import error_body, success_body


def test_success_body_minimal():
    b = success_body()
    assert b["success"] is True
    assert b["message"] == "ok"
    assert b["status_code"] == 200
    assert "data" not in b


def test_success_body_with_data_and_extra():
    b = success_body(data={"id": 1}, message="created", status_code=201, extra={"version": 2})
    assert b["success"] is True
    assert b["data"] == {"id": 1}
    assert b["status_code"] == 201
    assert b["version"] == 2


def test_error_body():
    b = error_body("bad", status_code=422)
    assert b["success"] is False
    assert b["message"] == "bad"
    assert b["status_code"] == 422

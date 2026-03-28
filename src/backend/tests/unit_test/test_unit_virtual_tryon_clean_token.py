"""virtual_tryon_service.clean_token (no ComfyUI)."""
from app.services.virtual_tryon_service import clean_token


def test_clean_token_none_and_quotes():
    assert clean_token(None) == ""
    assert clean_token('  "abc"  ') == "abc"
    assert clean_token("  'x' ") == "x"


def test_clean_token_strips_whitespace():
    assert clean_token("  tok\n") == "tok"

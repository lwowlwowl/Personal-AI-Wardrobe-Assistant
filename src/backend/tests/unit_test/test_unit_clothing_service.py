"""Unit: clothing upload helpers (FR-02, FR-03 tag list parsing partial)."""
import json

import pytest

from app.services.clothing_service import normalize_category, parse_season_form


def test_normalize_category_maps_unknown_to_other():
    assert normalize_category(None) == "other"
    assert normalize_category("") == "other"
    assert normalize_category("  TOP  ") == "top"
    assert normalize_category("not-a-real-category") == "other"


def test_parse_season_form_json_array():
    assert parse_season_form(json.dumps(["spring", "summer"])) == ["spring", "summer"]


def test_parse_season_form_empty():
    assert parse_season_form(None) is None
    assert parse_season_form("") is None


def test_parse_season_form_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_season_form("not-json")

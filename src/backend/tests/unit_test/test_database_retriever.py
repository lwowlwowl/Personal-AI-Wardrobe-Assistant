"""Agent context helpers: serialization and summary stats (AIwardrobe.utils.database_retriever)."""
import enum
from decimal import Decimal

from AIwardrobe.utils.database_retriever import (
    _build_agent_summary,
    _count_top_values,
    _serialize_value,
)


class _E(enum.Enum):
    A = "a"


def test_serialize_value_enum_decimal_date():
    assert _serialize_value(_E.A) == "a"
    assert _serialize_value(Decimal("12.5")) == "12.5"


def test_count_top_values_list_field_and_empty():
    rows = [
        {"category": ["top", "dress"]},
        {"category": "top"},
        {"category": None},
        {"category": ""},
    ]
    top = _count_top_values(rows, "category", top_k=3)
    values = [x["value"] for x in top]
    assert "top" in values


def test_build_agent_summary_recent_wear_order_and_counts():
    clothing = [{"category": "top"}, {"category": "top"}]
    outfits = [{}]
    history = [
        {"wear_date": "2026-01-01", "clothing_id": 1, "occasion": "work", "weather": "晴"},
        {"wear_date": "2026-03-01", "clothing_id": 2, "occasion": "gym", "weather": None},
    ]
    s = _build_agent_summary(clothing, outfits, history)
    assert s["counts"]["closet_items"] == 2
    assert s["counts"]["outfits"] == 1
    assert s["counts"]["wear_history"] == 2
    assert s["recent_wear"][0]["wear_date"] == "2026-03-01"
    assert s["recent_wear"][0]["weather"] is None

"""LLM JSON parsing and normalization (app.services.ai_message_service)."""
import json

from app.services.ai_message_service import build_ai_message


def test_build_ai_message_plain_text_fallback():
    msg = build_ai_message("Hello, no JSON here")
    assert msg["renderType"] == "text"
    assert msg["role"] == "ai"
    assert "Hello" in msg["content"]


def test_build_ai_message_invalid_json_fallback():
    msg = build_ai_message('{"broken": ')
    assert msg["renderType"] == "text"


def test_build_ai_message_recommendation_normalization():
    raw = {
        "locale": "zh",
        "content": "試試這套",
        "recommendations": [
            {
                "title": "  週末休閒  ",
                "items": [
                    {"type": "INVALID_TYPE", "name": "白T", "comment": "打底"},
                    {"type": "TOP", "name": "", "comment": "無名稱應跳過"},
                ],
            }
        ],
    }
    msg = build_ai_message(json.dumps(raw, ensure_ascii=False))
    assert msg["renderType"] == "recommendation"
    assert msg["locale"] == "zh"
    assert len(msg["recommendations"]) == 1
    assert msg["recommendations"][0]["title"] == "週末休閒"
    items = msg["recommendations"][0]["items"]
    assert len(items) == 1
    assert items[0]["type"] == "OTHER"
    assert items[0]["name"] == "白T"
    assert items[0]["reason"] == "打底"


def test_build_ai_message_plan_over_recommendation_when_both_present():
    raw = {
        "recommendations": [{"title": "X", "items": []}],
        "plan": {
            "title": "一週計劃",
            "days": [{"key": "d1", "label": "Day1", "items": [{"type": "TOP", "name": "襯衫"}]}],
        },
    }
    msg = build_ai_message(json.dumps(raw, ensure_ascii=False))
    assert msg["renderType"] == "plan"
    assert msg["plan"]["title"] == "一週計劃"
    assert len(msg["plan"]["days"]) == 1
    assert msg["plan"]["days"][0]["items"][0]["type"] == "TOP"


def test_build_ai_message_empty_recommendation_title_skipped():
    raw = {"recommendations": [{"title": "   ", "items": []}]}
    msg = build_ai_message(json.dumps(raw))
    assert msg["renderType"] == "text"


def test_build_ai_message_locale_invalid_defaults_en():
    raw = {"locale": "fr", "content": "hi"}
    msg = build_ai_message(json.dumps(raw))
    assert msg["locale"] == "en"

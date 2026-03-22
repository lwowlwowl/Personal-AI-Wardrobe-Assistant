import json
from typing import Any, Dict, List, Optional

ALLOWED_ITEM_TYPES = {
    "TOP", "BOTTOM", "DRESS", "OUTERWEAR", "FOOTWEAR",
    "ACCESSORY", "BAG", "UNDERWEAR", "OTHER"
}


def build_ai_message(raw_text: str) -> dict:
    parsed = _try_parse_json(raw_text)
    if parsed:
        normalized = _normalize_json_response(parsed, raw_text)
        if normalized:
            return normalized

    return _build_fallback_text_message(raw_text)


def _try_parse_json(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text or not isinstance(raw_text, str):
        return None
    try:
        data = json.loads(raw_text.strip())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _normalize_json_response(data: Dict[str, Any], raw_text: str) -> Optional[dict]:
    locale = str(data.get("locale") or "en").strip().lower()
    if locale not in {"en", "zh"}:
        locale = "en"

    content = str(data.get("content") or "").strip()

    # 先解析真实结构（不依赖 response_type，避免 LLM 写错 response_type 导致推荐/计划被丢掉）
    recommendations = _normalize_recommendations(data.get("recommendations"))
    plan = _normalize_plan(data.get("plan"))

    # 1. 结构优先：plan
    if plan and plan.get("days"):
        return {
            "role": "ai",
            "renderType": "plan",
            "rawText": raw_text.strip(),
            "content": content or (plan.get("intro") or ""),
            "recommendations": [],
            "plan": plan,
            "locale": locale,
        }

    # 2. 结构优先：recommendation
    if recommendations:
        return {
            "role": "ai",
            "renderType": "recommendation",
            "rawText": raw_text.strip(),
            "content": content,
            "recommendations": recommendations,
            "plan": None,
            "locale": locale,
        }

    # 3. 没有结构内容时，按 text 处理
    return {
        "role": "ai",
        "renderType": "text",
        "rawText": raw_text.strip(),
        "content": content or raw_text.strip(),
        "recommendations": [],
        "plan": None,
        "locale": locale,
    }


def _normalize_recommendations(value: Any) -> List[dict]:
    if not isinstance(value, list):
        return []

    result = []
    for rec in value:
        if not isinstance(rec, dict):
            continue

        items = _normalize_items(rec.get("items"), with_comment=True)
        # 允许 items 为空：风格诊断/分析类推荐可能只有 title、scenario、whyThisWorks 等，无具体单品
        title = str(rec.get("title") or "Outfit Recommendation").strip()
        if not title:
            continue

        result.append({
            "title": title,
            "scenario": str(rec.get("scenario") or "").strip(),
            "strategy": str(rec.get("strategy") or "").strip(),
            "styleTags": _string_list(rec.get("styleTags")),
            "items": items,
            "whyThisWorks": _string_list(rec.get("whyThisWorks")),
            "cautions": _string_list(rec.get("cautions")),
            "alternatives": _string_list(rec.get("alternatives")),
            "footer": str(rec.get("footer") or "").strip(),
        })

    return result


def _normalize_plan(value: Any) -> Optional[dict]:
    if not isinstance(value, dict):
        return None

    days_raw = value.get("days")
    if not isinstance(days_raw, list):
        return None

    days = []
    for i, day in enumerate(days_raw):
        if not isinstance(day, dict):
            continue

        items = _normalize_items(day.get("items"), with_comment=False)
        days.append({
            "key": str(day.get("key") or f"day-{i}"),
            "label": str(day.get("label") or f"Day {i+1}").strip(),
            "dateText": _optional_str(day.get("dateText")),
            "weatherText": _optional_str(day.get("weatherText")),
            "items": items,
            "notes": _optional_str(day.get("notes")),
        })

    return {
        "title": str(value.get("title") or "Outfit Plan").strip(),
        "intro": _optional_str(value.get("intro")),
        "days": days,
    }


def _normalize_items(value: Any, with_comment: bool) -> List[dict]:
    if not isinstance(value, list):
        return []

    items = []
    for item in value:
        if not isinstance(item, dict):
            continue

        item_type = str(item.get("type") or "OTHER").strip().upper()
        if item_type not in ALLOWED_ITEM_TYPES:
            item_type = "OTHER"

        comment_str = str(item.get("comment") or "").strip()
        normalized = {
            "type": item_type,
            "name": str(item.get("name") or "").strip(),
            "clothingId": item.get("clothingId"),
        }

        if with_comment:
            normalized["comment"] = comment_str
            # 前端 RecommendationCard 使用 reason 显示说明，保留兼容
            normalized["reason"] = comment_str

        if normalized["name"]:
            items.append(normalized)

    return items


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if str(x).strip()]


def _optional_str(value: Any) -> Optional[str]:
    text = str(value).strip() if value is not None else ""
    return text or None


def _build_fallback_text_message(raw_text: str) -> dict:
    text = (raw_text or "").strip() or "Sorry, I could not generate a valid response."
    return {
        "role": "ai",
        "renderType": "text",
        "rawText": text,
        "content": text,
        "recommendations": [],
        "plan": None,
        "locale": "en",
    }

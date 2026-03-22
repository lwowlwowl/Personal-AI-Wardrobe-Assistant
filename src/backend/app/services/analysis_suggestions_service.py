"""
衣櫥分析：AI 建議新增單品（不含 HTTP 路由）。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from AIwardrobe.model.factory import chat_model
from AIwardrobe.utils.database_retriever import build_agent_context


def build_suggested_additions_context(user_id: int, db: Session) -> dict[str, Any]:
    context = build_agent_context(
        user_id=user_id,
        db=db,
        closet_limit=120,
        outfit_limit=40,
        wear_history_limit=80,
        include_summary=True,
    )

    closet_items = context.get("closet_items", [])
    summary = context.get("summary", {})
    sample_items = sorted(
        closet_items,
        key=lambda item: (
            -(item.get("wear_count") or 0),
            item.get("name") or "",
        ),
    )[:24]

    compact_items = [
        {
            "name": item.get("name"),
            "category": item.get("category"),
            "style": item.get("style"),
            "color": item.get("color"),
            "season": item.get("season"),
            "wear_count": item.get("wear_count"),
            "last_worn_date": item.get("last_worn_date"),
            "is_favorite": item.get("is_favorite"),
        }
        for item in sample_items
    ]

    return {
        "summary": summary,
        "sample_items": compact_items,
    }


def parse_suggested_additions_content(content: str) -> list[str]:
    raw = (content or "").strip()
    if not raw:
        return []

    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return []

    if not isinstance(parsed, list):
        return []

    items: list[str] = []
    for item in parsed:
        text = str(item).strip()
        if text:
            items.append(text)

    return items[:3]


async def generate_suggested_additions(prompt_context: dict[str, Any]) -> list[str]:
    system_prompt = (
        "You are a senior wardrobe analysis advisor. "
        "From the user's wardrobe summary, propose exactly 3 items to add. "
        "Write everything in English only. "
        "Each item is one string with this exact shape: "
        "\"Short actionable title (about 8–18 words) | One or two sentences explaining why it fits their closet.\" "
        "The title should read like “Add a …” or “Consider a …” and name a specific garment type; "
        "the part after the pipe explains the gap it fills. "
        "Separate title and rationale with a single ASCII pipe surrounded by spaces: \" | \". "
        "Do not include brands, prices, purchase links, bullet numbers, or Markdown. "
        "Return only a JSON array of three strings, for example "
        "[\"Add a … | …\", \"Add a … | …\", \"Add a … | …\"]."
    )
    user_prompt = json.dumps(prompt_context, ensure_ascii=False, indent=2)

    response = await chat_model.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "Wardrobe context is below. Reply with the JSON array only, no other text:\n"
                    f"{user_prompt}"
                )
            ),
        ]
    )
    return parse_suggested_additions_content(getattr(response, "content", ""))


async def run_suggested_additions(db: Session, user_id: int, limit: int) -> Dict[str, Any]:
    prompt_context = build_suggested_additions_context(user_id, db)
    closet_count = prompt_context.get("summary", {}).get("counts", {}).get("closet_items", 0)

    if not closet_count:
        items: List[str] = []
    else:
        items = await generate_suggested_additions(prompt_context)

    if len(items) > limit:
        items = items[:limit]

    return {
        "success": True,
        "message": "Suggested additions loaded successfully",
        "data": {
            "items": items[:limit],
        },
        "status_code": 200,
    }

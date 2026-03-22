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
        "你是一名资深衣橱分析顾问。"
        "请基于用户衣橱摘要，给出 3 条建议新增的单品建议。"
        "每条建议都必须是纯中文一句话，20 到 40 个字，包含“建议补一件/一条/一双”这类明确单品方向，"
        "并说明为什么适合当前衣橱。"
        "不要输出品牌、价格、购买链接、编号、Markdown。"
        "只返回 JSON 数组字符串，例如 "
        "[\"建议补一件...\", \"建议补一条...\", \"建议补一双...\"]。"
    )
    user_prompt = json.dumps(prompt_context, ensure_ascii=False, indent=2)

    response = await chat_model.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户衣橱摘要如下，请直接返回 JSON 数组：\n{user_prompt}"),
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
        "message": "获取推荐添加成功",
        "data": {
            "items": items[:limit],
        },
        "status_code": 200,
    }

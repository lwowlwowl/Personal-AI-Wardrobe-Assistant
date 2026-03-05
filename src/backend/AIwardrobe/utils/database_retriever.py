"""
数据库读取工具。

为项目中的 7 张业务表提供基础读取函数。
返回值统一为可直接序列化的字典列表，便于被接口层或其他服务直接复用。
"""

from __future__ import annotations

import enum
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterator, Optional

from sqlalchemy import inspect
from sqlalchemy.orm import Session, load_only

from database import SessionLocal
from models import (
    ClothingItem,
    ClothingTag,
    ModelPhoto,
    Outfit,
    OutfitItem,
    User,
    WearHistory,
)


@contextmanager
def _session_scope(db: Optional[Session] = None) -> Iterator[Session]:
    """
    统一管理数据库会话。

    如果调用方已经传入会话，则复用该会话；
    否则创建临时会话并在使用完毕后关闭。
    """
    session = db or SessionLocal()
    try:
        yield session
    finally:
        if db is None:
            session.close()


def _serialize_value(value: Any) -> Any:
    """将 ORM 字段值转换成便于 JSON 序列化的基础类型。"""
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_serialize_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def _serialize_model(
    instance: Any,
    exclude_fields: Optional[set[str]] = None
) -> dict[str, Any]:
    """只序列化表字段，避免把 relationship 一并展开。"""
    exclude_fields = exclude_fields or set()
    return {
        column.name: _serialize_value(getattr(instance, column.name))
        for column in instance.__table__.columns
        if column.name not in exclude_fields
    }


def _fetch_all(
    model: Any,
    db: Optional[Session] = None,
    filters: Optional[dict[str, Any]] = None,
    exclude_fields: Optional[set[str]] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """
    通用表读取逻辑。

    Args:
        model: SQLAlchemy 模型类
        db: 可选的外部数据库会话
        filters: 使用 filter_by 的等值过滤条件
        exclude_fields: 排除返回（且避免查询）的字段名集合
        limit: 最大返回条数，None 表示不限制
        offset: 分页偏移量
    """
    filters = {key: value for key, value in (filters or {}).items() if value is not None}
    exclude_fields = exclude_fields or set()

    with _session_scope(db) as session:
        query = session.query(model)

        if exclude_fields:
            mapper = inspect(model)
            included_columns = []
            for attr in mapper.column_attrs:
                if attr.key not in exclude_fields:
                    included_columns.append(getattr(model, attr.key))

            if included_columns:
                query = query.options(load_only(*included_columns))

        if filters:
            query = query.filter_by(**filters)

        if hasattr(model, "id"):
            query = query.order_by(model.id)

        if offset > 0:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return [
            _serialize_model(record, exclude_fields=exclude_fields)
            for record in query.all()
        ]


def get_users(
    db: Optional[Session] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `users` 表数据。"""
    return _fetch_all(
        User,
        db=db,
        filters={"is_active": is_active},
        exclude_fields={"email", "hashed_password"},
        limit=limit,
        offset=offset,
    )


def get_clothing_items(
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `clothing_items` 表数据。"""
    return _fetch_all(
        ClothingItem,
        db=db,
        filters={"user_id": user_id},
        limit=limit,
        offset=offset,
    )


def get_clothing_tags(
    db: Optional[Session] = None,
    clothing_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `clothing_tags` 表数据。"""
    return _fetch_all(
        ClothingTag,
        db=db,
        filters={"clothing_id": clothing_id},
        limit=limit,
        offset=offset,
    )


def get_model_photos(
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `model_photos` 表数据。"""
    return _fetch_all(
        ModelPhoto,
        db=db,
        filters={"user_id": user_id},
        limit=limit,
        offset=offset,
    )


def get_outfits(
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `outfits` 表数据。"""
    return _fetch_all(
        Outfit,
        db=db,
        filters={"user_id": user_id},
        limit=limit,
        offset=offset,
    )


def get_outfit_items(
    db: Optional[Session] = None,
    outfit_id: Optional[int] = None,
    clothing_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `outfit_items` 表数据。"""
    return _fetch_all(
        OutfitItem,
        db=db,
        filters={"outfit_id": outfit_id, "clothing_id": clothing_id},
        limit=limit,
        offset=offset,
    )


def get_wear_history(
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    clothing_id: Optional[int] = None,
    outfit_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> list[dict[str, Any]]:
    """读取 `wear_history` 表数据。"""
    return _fetch_all(
        WearHistory,
        db=db,
        filters={
            "user_id": user_id,
            "clothing_id": clothing_id,
            "outfit_id": outfit_id,
        },
        limit=limit,
        offset=offset,
    )


def _count_top_values(
    rows: list[dict[str, Any]],
    field: str,
    top_k: int = 5
) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        if value is None:
            continue

        if isinstance(value, list):
            for item in value:
                if item:
                    counter[str(item)] += 1
            continue

        if value != "":
            counter[str(value)] += 1

    return [{"value": item, "count": count} for item, count in counter.most_common(top_k)]


def _build_agent_summary(
    clothing_items: list[dict[str, Any]],
    outfits: list[dict[str, Any]],
    wear_history: list[dict[str, Any]]
) -> dict[str, Any]:
    recent_wear = sorted(
        wear_history,
        key=lambda row: row.get("wear_date") or "",
        reverse=True
    )[:10]

    return {
        "counts": {
            "closet_items": len(clothing_items),
            "outfits": len(outfits),
            "wear_history": len(wear_history),
        },
        "top_categories": _count_top_values(clothing_items, "category"),
        "top_colors": _count_top_values(clothing_items, "color"),
        "top_occasions": _count_top_values(wear_history, "occasion"),
        "recent_wear": [
            {
                "wear_date": row.get("wear_date"),
                "clothing_id": row.get("clothing_id"),
                "outfit_id": row.get("outfit_id"),
                "occasion": row.get("occasion"),
                "weather": row.get("weather"),
                "rating": row.get("rating"),
            }
            for row in recent_wear
        ],
    }


def build_agent_context(
    user_id: int,
    db: Optional[Session] = None,
    closet_limit: int = 100,
    closet_offset: int = 0,
    outfit_limit: int = 50,
    outfit_offset: int = 0,
    wear_history_limit: int = 100,
    wear_history_offset: int = 0,
    include_summary: bool = True,
    constraints: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    构建给 Agent 的用户上下文。

    采用“先摘要后明细”的结构，并默认排除用户敏感字段。
    """
    if user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    user_rows = _fetch_all(
        User,
        db=db,
        filters={"id": user_id},
        exclude_fields={"email", "hashed_password"},
        limit=1,
    )
    if not user_rows:
        raise ValueError(f"user not found: {user_id}")

    user = user_rows[0]
    user_payload = {
        "id": user.get("id"),
        "username": user.get("username"),
        "is_active": user.get("is_active"),
        "created_at": user.get("created_at"),
    }

    clothing_items = get_clothing_items(
        db=db,
        user_id=user_id,
        limit=closet_limit,
        offset=closet_offset,
    )
    outfits = get_outfits(
        db=db,
        user_id=user_id,
        limit=outfit_limit,
        offset=outfit_offset,
    )
    wear_history = get_wear_history(
        db=db,
        user_id=user_id,
        limit=wear_history_limit,
        offset=wear_history_offset,
    )

    payload: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "user": user_payload,
        "closet_items": clothing_items,
        "outfits": outfits,
        "wear_history": wear_history,
        "constraints": constraints or {},
        "pagination": {
            "closet_items": {"limit": closet_limit, "offset": closet_offset, "count": len(clothing_items)},
            "outfits": {"limit": outfit_limit, "offset": outfit_offset, "count": len(outfits)},
            "wear_history": {"limit": wear_history_limit, "offset": wear_history_offset, "count": len(wear_history)},
        },
    }

    if include_summary:
        payload["summary"] = _build_agent_summary(clothing_items, outfits, wear_history)

    return payload


__all__ = [
    "get_users",
    "get_clothing_items",
    "get_clothing_tags",
    "get_model_photos",
    "get_outfits",
    "get_outfit_items",
    "get_wear_history",
    "build_agent_context",
]

if __name__ == "__main__":
    print(get_users())
    print(get_outfits())
    print(get_outfit_items())
    print(get_model_photos())
    print(get_wear_history())
    print(get_clothing_items())
    print(get_clothing_tags())
    print(build_agent_context(1))
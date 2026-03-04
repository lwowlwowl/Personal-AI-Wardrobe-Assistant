"""
数据库读取工具。

为项目中的 7 张业务表提供基础读取函数。
返回值统一为可直接序列化的字典列表，便于被接口层或其他服务直接复用。
"""

from __future__ import annotations

import enum
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterator, Optional

from sqlalchemy.orm import Session

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


def _serialize_model(instance: Any) -> dict[str, Any]:
    """只序列化表字段，避免把 relationship 一并展开。"""
    return {
        column.name: _serialize_value(getattr(instance, column.name))
        for column in instance.__table__.columns
    }


def _fetch_all(
    model: Any,
    db: Optional[Session] = None,
    filters: Optional[dict[str, Any]] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    通用表读取逻辑。

    Args:
        model: SQLAlchemy 模型类
        db: 可选的外部数据库会话
        filters: 使用 filter_by 的等值过滤条件
        limit: 最大返回条数，None 表示不限制
        offset: 分页偏移量
    """
    filters = {key: value for key, value in (filters or {}).items() if value is not None}

    with _session_scope(db) as session:
        query = session.query(model)

        if filters:
            query = query.filter_by(**filters)

        if hasattr(model, "id"):
            query = query.order_by(model.id)

        if offset > 0:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return [_serialize_model(record) for record in query.all()]


def get_users(
    db: Optional[Session] = None,
    is_active: Optional[bool] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """读取 `users` 表数据。"""
    return _fetch_all(
        User,
        db=db,
        filters={"is_active": is_active},
        limit=limit,
        offset=offset,
    )


def get_clothing_items(
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: int = 0,
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
    offset: int = 0,
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
    offset: int = 0,
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
    offset: int = 0,
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
    offset: int = 0,
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
    offset: int = 0,
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


__all__ = [
    "get_users",
    "get_clothing_items",
    "get_clothing_tags",
    "get_model_photos",
    "get_outfits",
    "get_outfit_items",
    "get_wear_history",
]

if __name__ == "__main__":
    print(get_users())

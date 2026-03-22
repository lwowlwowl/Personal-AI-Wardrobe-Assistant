"""
衣櫥分析：閒置、顏色/風格統計、最常穿、本週活躍度（不含 HTTP 路由）。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

import app.models as models

# 前端 Weekly Activity 分类显示名与图标（与衣橱主分类一致，含 Bag 独立展示）
_WEEKLY_ACTIVITY_CATEGORY_MAP = {
    "top": {"name": "Tops", "icon": "👕"},
    "bottom": {"name": "Bottoms", "icon": "👖"},
    "dress": {"name": "Dress", "icon": "👗"},
    "outerwear": {"name": "Outerwear", "icon": "🧥"},
    "footwear": {"name": "Footwear", "icon": "👟"},
    "accessory": {"name": "Accessories", "icon": "⌚"},
    "bag": {"name": "Bag", "icon": "👜"},
    "underwear": {"name": "Underwear", "icon": "🩲"},
    "other": {"name": "Other", "icon": "📦"},
}
_WEEK_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def run_idle_rate(db: Session, user_id: int, days: int) -> Dict[str, Any]:
    cutoff_date = datetime.now() - timedelta(days=days)
    today = date.today()

    total_items = (
        db.query(func.count(models.ClothingItem.id)).filter(models.ClothingItem.user_id == user_id).scalar() or 0
    )

    idle_items = (
        db.query(func.count(models.ClothingItem.id))
        .filter(
            models.ClothingItem.user_id == user_id,
            (
                (models.ClothingItem.wear_count == 0)
                | (models.ClothingItem.last_worn_date < cutoff_date)
                | (models.ClothingItem.last_worn_date.is_(None))
            ),
        )
        .scalar()
        or 0
    )

    idle_rate = round((idle_items / total_items * 100), 1) if total_items > 0 else 0

    most_idle_items = (
        db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.wear_count,
            models.ClothingItem.last_worn_date,
        )
        .filter(models.ClothingItem.user_id == user_id)
        .order_by(models.ClothingItem.last_worn_date.asc().nullsfirst())
        .limit(10)
        .all()
    )

    most_idle_items_data = []
    for item in most_idle_items:
        if item.last_worn_date:
            days_since_last_worn = (today - item.last_worn_date).days
        else:
            days_since_last_worn = days * 2

        most_idle_items_data.append(
            {
                "id": item.id,
                "name": item.name,
                "image_url": item.image_url,
                "wear_count": item.wear_count,
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
                "days_since_last_worn": days_since_last_worn,
            }
        )

    return {
        "success": True,
        "data": {
            "total_items": total_items,
            "idle_items": idle_items,
            "idle_rate": idle_rate,
            "threshold_days": days,
            "most_idle_items": most_idle_items_data,
        },
    }


def run_idle_items_detail(
    db: Session,
    user_id: int,
    page: int,
    page_size: int,
    time_filter: Optional[str],
    season_filter: Optional[str],
) -> Dict[str, Any]:
    today = date.today()

    query = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == user_id)

    if time_filter is None:
        cutoff_date = today - timedelta(days=30)
        query = query.filter(
            (models.ClothingItem.wear_count == 0)
            | (models.ClothingItem.last_worn_date < cutoff_date)
            | (models.ClothingItem.last_worn_date.is_(None))
        )
    elif time_filter == "never":
        query = query.filter(models.ClothingItem.wear_count == 0)
    elif time_filter == "over_season":
        cutoff = today - timedelta(days=90)
        query = query.filter(models.ClothingItem.last_worn_date < cutoff, models.ClothingItem.wear_count > 0)
    elif time_filter == "over_year":
        cutoff = today - timedelta(days=365)
        query = query.filter(models.ClothingItem.last_worn_date < cutoff, models.ClothingItem.wear_count > 0)
    elif time_filter == "over_six_months":
        cutoff = today - timedelta(days=180)
        query = query.filter(models.ClothingItem.last_worn_date < cutoff, models.ClothingItem.wear_count > 0)
    elif time_filter == "over_three_months":
        cutoff = today - timedelta(days=90)
        query = query.filter(models.ClothingItem.last_worn_date < cutoff, models.ClothingItem.wear_count > 0)

    if season_filter and season_filter != "all":
        try:
            season_enum = models.ClothingSeason(season_filter)
            query = query.filter(models.ClothingItem.season.contains([season_enum]))
        except ValueError:
            pass

    total = query.count()
    skip = (page - 1) * page_size
    rows = (
        query.order_by(models.ClothingItem.last_worn_date.asc().nullsfirst()).offset(skip).limit(page_size).all()
    )

    items = []
    for row in rows:
        season_val = None
        if getattr(row, "season", None) is not None:
            try:
                season_val = [s.value if hasattr(s, "value") else str(s) for s in row.season]
            except Exception:
                season_val = []
        items.append(
            {
                "id": row.id,
                "name": row.name,
                "image_url": getattr(row, "image_url", None) or "",
                "wear_count": getattr(row, "wear_count", 0) or 0,
                "last_worn_date": row.last_worn_date.isoformat()
                if getattr(row, "last_worn_date", None)
                else None,
                "season": season_val,
                "category": getattr(row, "category", None).value
                if getattr(row, "category", None) is not None and hasattr(row.category, "value")
                else None,
                "color": getattr(row, "color", None),
                "color_code": getattr(row, "color_code", None),
            }
        )

    return {
        "success": True,
        "data": {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        },
    }


def run_top_color(db: Session, user_id: int) -> Dict[str, Any]:
    color_counts = (
        db.query(models.ClothingItem.color, func.count(models.ClothingItem.id).label("count"))
        .filter(models.ClothingItem.user_id == user_id, models.ClothingItem.color.isnot(None))
        .group_by(models.ClothingItem.color)
        .order_by(func.count(models.ClothingItem.id).desc())
        .all()
    )

    total_items_with_color = (
        db.query(func.count(models.ClothingItem.id))
        .filter(models.ClothingItem.user_id == user_id, models.ClothingItem.color.isnot(None))
        .scalar()
        or 0
    )

    color_name_map = {
        "white": "White",
        "black": "Black",
        "gray": "Gray",
        "grey": "Gray",
        "brown": "Brown",
        "beige": "Beige",
        "navy": "Navy",
        "blue": "Blue",
        "red": "Red",
        "green": "Green",
        "yellow": "Yellow",
        "pink": "Pink",
        "purple": "Purple",
        "orange": "Orange",
        "multicolor": "Multicolor",
    }

    top_color_data = []
    for color_item in color_counts:
        top_color_data.append(
            {
                "color_code": color_item.color,
                "color_name": color_name_map.get(color_item.color, color_item.color),
                "count": color_item.count,
                "percentage": round((color_item.count / total_items_with_color * 100), 1)
                if total_items_with_color > 0
                else 0,
            }
        )

    top_color = (
        top_color_data[0]
        if top_color_data
        else {"color_code": "brown", "color_name": "Brown", "count": 0, "percentage": 0}
    )

    return {
        "success": True,
        "data": {
            "top_color": top_color,
            "color_distribution": top_color_data,
            "total_items_with_color": total_items_with_color,
        },
    }


def run_top_style(db: Session, user_id: int) -> Dict[str, Any]:
    style_tags = (
        db.query(models.ClothingTag.tag, func.count(models.ClothingTag.id).label("count"))
        .join(models.ClothingItem, models.ClothingItem.id == models.ClothingTag.clothing_id)
        .filter(
            models.ClothingItem.user_id == user_id,
            models.ClothingTag.tag.in_(
                [
                    "sporty",
                    "casual",
                    "formal",
                    "business",
                    "minimal",
                    "bohemian",
                    "vintage",
                    "streetwear",
                    "运动",
                    "休闲",
                    "正式",
                    "商务",
                    "简约",
                    "波西米亚",
                    "复古",
                    "街头",
                ]
            ),
        )
        .group_by(models.ClothingTag.tag)
        .order_by(func.count(models.ClothingTag.id).desc())
        .all()
    )

    style_name_map = {
        "sporty": "Sporty",
        "casual": "Casual",
        "formal": "Formal",
        "business": "Business",
        "minimal": "Minimal",
        "bohemian": "Bohemian",
        "vintage": "Vintage",
        "streetwear": "Streetwear",
        "运动": "Sporty",
        "休闲": "Casual",
        "正式": "Formal",
        "商务": "Business",
        "简约": "Minimal",
        "波西米亚": "Bohemian",
        "复古": "Vintage",
        "街头": "Streetwear",
    }

    total_styles = sum(item.count for item in style_tags) or 1

    style_data = []
    for style_item in style_tags:
        style_data.append(
            {
                "style_code": style_item.tag,
                "style_name": style_name_map.get(style_item.tag, style_item.tag),
                "count": style_item.count,
                "percentage": round((style_item.count / total_styles * 100), 1),
            }
        )

    top_style = (
        style_data[0]
        if style_data
        else {"style_code": "casual", "style_name": "Casual", "count": 0, "percentage": 0}
    )

    return {
        "success": True,
        "data": {
            "top_style": top_style,
            "style_distribution": style_data,
            "total_styles_count": total_styles,
        },
    }


def run_most_worn_items(db: Session, user_id: int, time_range: str, limit: int) -> Dict[str, Any]:
    try:
        now = datetime.now()
        today = date.today()

        if time_range == "yearly":
            start_date = date(now.year, 1, 1)
            date_range_text = f"今年 ({now.year}年)"
        elif time_range == "monthly":
            start_date = date(now.year, now.month, 1)
            date_range_text = f"本月 ({now.year}年{now.month}月)"
        elif time_range == "weekly":
            start_date = today - timedelta(days=7)
            date_range_text = f"近7天 ({start_date.isoformat()} 起)"
        else:
            start_date = today
            date_range_text = f"今天 ({today.isoformat()})"

        items = (
            db.query(
                models.ClothingItem.id,
                models.ClothingItem.name,
                models.ClothingItem.color,
                models.ClothingItem.wear_count,
                models.ClothingItem.last_worn_date,
                models.ClothingItem.created_at,
            )
            .filter(models.ClothingItem.user_id == user_id)
            .all()
        )

        if not items:
            return {
                "success": True,
                "data": {
                    "items": [],
                    "time_range": time_range,
                    "date_range": date_range_text,
                },
            }

        most_worn_data = []

        for item in items:
            item_data = {
                "id": item.id,
                "name": item.name,
                "color": item.color or "gray",
                "total_wear_count": item.wear_count,
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
            }

            wears_in_range = 0

            if item.last_worn_date:
                last_worn = item.last_worn_date
                if hasattr(last_worn, "date"):
                    last_worn = last_worn.date()

                if last_worn >= start_date:
                    if time_range == "daily":
                        wears_in_range = item.wear_count if last_worn == today else 0
                    elif time_range == "weekly":
                        wears_in_range = item.wear_count
                    elif time_range == "monthly":
                        wears_in_range = (
                            item.wear_count
                            if last_worn.month == now.month and last_worn.year == now.year
                            else 0
                        )
                    else:
                        wears_in_range = item.wear_count if last_worn.year == now.year else 0
                else:
                    wears_in_range = 0
            else:
                wears_in_range = 0

            item_data["wear_count"] = wears_in_range
            most_worn_data.append(item_data)

        most_worn_data.sort(key=lambda x: x["wear_count"], reverse=True)
        most_worn_data = most_worn_data[:limit]

        formatted_items = [
            {"name": item["name"], "wears": item["wear_count"], "color": item["color"]}
            for item in most_worn_data
        ]

        return {
            "success": True,
            "data": {
                "items": formatted_items,
                "time_range": time_range,
                "date_range": date_range_text,
                "total_items": len(items),
            },
        }

    except Exception:
        return {
            "success": True,
            "data": {
                "items": [
                    {"name": "示例物品1", "wears": 10, "color": "blue"},
                    {"name": "示例物品2", "wears": 8, "color": "black"},
                    {"name": "示例物品3", "wears": 5, "color": "white"},
                ],
                "time_range": time_range,
                "note": "返回了示例数据（后端出错）",
            },
        }


def run_weekly_activity(db: Session, user_id: int) -> Dict[str, Any]:
    today = date.today()
    this_week_monday = today - timedelta(days=today.weekday())
    this_week_sunday = this_week_monday + timedelta(days=6)
    last_week_monday = this_week_monday - timedelta(days=7)
    last_week_sunday = this_week_sunday - timedelta(days=7)

    q_this_week = db.query(func.count(models.WearHistory.id)).filter(
        models.WearHistory.user_id == user_id,
        models.WearHistory.wear_date >= this_week_monday,
        models.WearHistory.wear_date <= this_week_sunday,
        models.WearHistory.clothing_id.isnot(None),
    )
    total_wears_this_week = q_this_week.scalar() or 0

    q_last_week = db.query(func.count(models.WearHistory.id)).filter(
        models.WearHistory.user_id == user_id,
        models.WearHistory.wear_date >= last_week_monday,
        models.WearHistory.wear_date <= last_week_sunday,
        models.WearHistory.clothing_id.isnot(None),
    )
    total_wears_last_week = q_last_week.scalar() or 0

    if total_wears_last_week > 0:
        trend_percent = round(
            (total_wears_this_week - total_wears_last_week) / total_wears_last_week * 100
        )
    else:
        trend_percent = 0 if total_wears_this_week == 0 else 100

    daily_counts = (
        db.query(models.WearHistory.wear_date, func.count(models.WearHistory.id).label("cnt"))
        .filter(
            models.WearHistory.user_id == user_id,
            models.WearHistory.wear_date >= this_week_monday,
            models.WearHistory.wear_date <= this_week_sunday,
            models.WearHistory.clothing_id.isnot(None),
        )
        .group_by(models.WearHistory.wear_date)
        .all()
    )
    day_to_count = {d: c for d, c in daily_counts}
    week_data = [
        {"label": _WEEK_DAY_LABELS[i], "wears": day_to_count.get(this_week_monday + timedelta(days=i), 0)}
        for i in range(7)
    ]

    category_rows = (
        db.query(models.ClothingItem.category, func.count(models.WearHistory.id).label("cnt"))
        .join(models.WearHistory, models.WearHistory.clothing_id == models.ClothingItem.id)
        .filter(
            models.WearHistory.user_id == user_id,
            models.WearHistory.wear_date >= this_week_monday,
            models.WearHistory.wear_date <= this_week_sunday,
        )
        .group_by(models.ClothingItem.category)
        .all()
    )
    category_map_agg: Dict[str, Any] = {}
    for cat_enum, cnt in category_rows:
        cat_key = (cat_enum.value if hasattr(cat_enum, "value") else str(cat_enum)).lower()
        info = _WEEKLY_ACTIVITY_CATEGORY_MAP.get(cat_key, {"name": "Other", "icon": "📦"})
        name = info["name"]
        if name not in category_map_agg:
            category_map_agg[name] = {"name": name, "icon": info["icon"], "count": 0}
        category_map_agg[name]["count"] += cnt
    category_activity = list(category_map_agg.values())
    category_activity.sort(key=lambda x: -x["count"])

    return {
        "success": True,
        "data": {
            "total_wears_this_week": total_wears_this_week,
            "total_wears_last_week": total_wears_last_week,
            "trend_percent": trend_percent,
            "week_data": week_data,
            "category_activity": category_activity,
        },
        "status_code": 200,
    }

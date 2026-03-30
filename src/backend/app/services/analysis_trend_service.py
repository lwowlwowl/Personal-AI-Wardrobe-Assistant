"""
Wardrobe analytics: trends, summary, category distribution, export (no HTTP layer).
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy import Date, func
from sqlalchemy.orm import Session

import app.models as models


class TrendDataService:
    """Trend/summary analytics service (business logic only)."""

    @staticmethod
    def get_date_range(
        view_by: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[datetime, datetime]:
        now = datetime.now()

        if view_by == "yearly":
            if not start_date:
                start_date = datetime(now.year - 10, 1, 1)
            if not end_date:
                end_date = now

        elif view_by == "monthly":
            start_date = now - relativedelta(months=11)
            start_date = start_date.replace(day=1)
            end_date = now

        elif view_by == "daily":
            start_date = now - timedelta(days=29)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        elif view_by == "weekly":
            start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        else:
            raise ValueError(f"Unsupported view type: {view_by}")

        return start_date, end_date

    @staticmethod
    def generate_time_labels(view_by: str, start_date: datetime, end_date: datetime) -> List[str]:
        labels: List[str] = []
        current = start_date

        if view_by == "yearly":
            while current.year <= end_date.year:
                labels.append(str(current.year))
                current = current.replace(year=current.year + 1)

        elif view_by == "monthly":
            while current <= end_date:
                labels.append(current.strftime("%Y-%m"))
                current += relativedelta(months=1)

        elif view_by == "daily":
            while current <= end_date:
                labels.append(current.strftime("%m/%d"))
                current += timedelta(days=1)

        elif view_by == "weekly":
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for _ in range(7):
                labels.append(day_names[current.weekday()])
                current += timedelta(days=1)

        return labels

    @staticmethod
    def get_time_group_field(view_by: str):
        if view_by == "yearly":
            return func.extract("year", models.ClothingItem.created_at)
        if view_by == "monthly":
            return func.to_char(models.ClothingItem.created_at, "YYYY-MM")
        if view_by == "daily" or view_by == "weekly":
            return func.cast(models.ClothingItem.created_at, Date)
        return func.extract("year", models.ClothingItem.created_at)


def run_total_items_trend(
    db: Session,
    user_id: int,
    view_by: str,
    start_year: Optional[int],
    end_year: Optional[int],
    include_projection: bool,
) -> Dict[str, Any]:
    trend_service = TrendDataService()

    first_item = db.query(func.min(models.ClothingItem.created_at)).filter(
        models.ClothingItem.user_id == user_id,
    ).scalar()

    if not first_item:
        return {
            "success": True,
            "data": {
                "labels": [],
                "values": [],
                "increments": [],
                "view_by": view_by,
                "total_count": 0,
                "statistics": {},
            },
        }

    now = datetime.now()

    if view_by == "yearly":
        start_date = datetime(start_year or first_item.year, 1, 1)
        end_date = datetime(end_year or now.year, 12, 31)
    else:
        start_date, end_date = trend_service.get_date_range(view_by)

    group_field = trend_service.get_time_group_field(view_by)

    query = (
        db.query(
            group_field.label("time_period"),
            func.count(models.ClothingItem.id).label("increment"),
        )
        .filter(
            models.ClothingItem.user_id == user_id,
            models.ClothingItem.created_at.between(start_date, end_date),
        )
        .group_by(group_field)
        .order_by(group_field)
    )

    results = query.all()

    labels = trend_service.generate_time_labels(view_by, start_date, end_date)

    increment_map: Dict[str, int] = {}
    for r in results:
        if view_by == "yearly":
            key = str(int(r.time_period))
        elif view_by == "monthly":
            key = r.time_period
        else:
            key = (
                r.time_period.strftime("%Y-%m-%d")
                if hasattr(r.time_period, "strftime")
                else str(r.time_period)
            )
        increment_map[key] = r.increment

    increments: List[int] = []
    cumulative_values: List[int] = []
    base_count = (
        db.query(func.count(models.ClothingItem.id))
        .filter(
            models.ClothingItem.user_id == user_id,
            models.ClothingItem.created_at < start_date,
        )
        .scalar()
        or 0
    )
    total = base_count

    for i, label in enumerate(labels):
        if view_by == "yearly":
            key = label
        elif view_by == "monthly":
            key = label
        elif view_by == "weekly":
            key = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        else:
            try:
                month, day = map(int, label.split("/"))
                year = start_date.year
                if month == 1 and start_date.month == 12:
                    year = end_date.year
                key = datetime(year, month, day).strftime("%Y-%m-%d")
            except Exception:
                key = label

        increment = increment_map.get(key, 0)
        increments.append(increment)
        total += increment
        cumulative_values.append(total)

    statistics: Dict[str, Any] = {}
    if cumulative_values:
        if len(cumulative_values) > 1:
            growth_rates = []
            for j in range(1, len(cumulative_values)):
                if cumulative_values[j - 1] > 0:
                    rate = (cumulative_values[j] - cumulative_values[j - 1]) / cumulative_values[j - 1] * 100
                    growth_rates.append(rate)
            statistics["avg_growth"] = round(sum(growth_rates) / len(growth_rates), 2) if growth_rates else 0
        else:
            statistics["avg_growth"] = 0

        if increments:
            max_growth = max(increments)
            max_index = increments.index(max_growth)
            statistics["max_growth"] = max_growth
            statistics["max_period"] = labels[max_index] if max_index < len(labels) else None

        if include_projection and view_by == "yearly" and len(cumulative_values) >= 3:
            x = list(range(len(cumulative_values)))
            y = cumulative_values
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_xx = sum(x[i] * x[i] for i in range(n))

            if n * sum_xx - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                next_year = len(cumulative_values)
                projection = slope * next_year + intercept
                statistics["projection"] = round(projection)
                last_year = int(labels[-1]) if labels else now.year
                statistics["projection_year"] = last_year + 1

    return {
        "success": True,
        "data": {
            "labels": labels,
            "values": cumulative_values,
            "increments": increments,
            "view_by": view_by,
            "total_count": cumulative_values[-1] if cumulative_values else 0,
            "statistics": statistics,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        },
    }


def run_total_items_summary(db: Session, user_id: int) -> Dict[str, Any]:
    now = datetime.now()

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_end = month_start - timedelta(days=1)

    base_query = db.query(models.ClothingItem).filter(models.ClothingItem.user_id == user_id)

    total_items = base_query.count()
    total_value = (
        db.query(func.sum(models.ClothingItem.price)).filter(models.ClothingItem.user_id == user_id).scalar() or 0
    )
    categories_count = (
        db.query(func.count(func.distinct(models.ClothingItem.category)))
        .filter(models.ClothingItem.user_id == user_id)
        .scalar()
        or 0
    )

    today_new = base_query.filter(models.ClothingItem.created_at >= today_start).count()
    week_new = base_query.filter(models.ClothingItem.created_at >= week_start).count()
    month_new = base_query.filter(models.ClothingItem.created_at >= month_start).count()
    year_new = base_query.filter(models.ClothingItem.created_at >= year_start).count()
    last_month_new = base_query.filter(
        models.ClothingItem.created_at.between(last_month_start, last_month_end)
    ).count()

    latest_items = (
        db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.created_at,
        )
        .filter(models.ClothingItem.user_id == user_id)
        .order_by(models.ClothingItem.created_at.desc())
        .limit(5)
        .all()
    )

    growth_rate = 0
    if last_month_new > 0:
        growth_rate = round(((month_new - last_month_new) / last_month_new) * 100, 1)

    return {
        "success": True,
        "data": {
            "total_items": total_items,
            "total_value": float(total_value),
            "categories_count": categories_count,
            "latest_added": [
                {
                    "id": item.id,
                    "name": item.name,
                    "image_url": item.image_url,
                    "created_at": item.created_at.isoformat(),
                }
                for item in latest_items
            ],
            "growth_rate": growth_rate,
            "stats_by_period": {
                "today": today_new,
                "this_week": week_new,
                "this_month": month_new,
                "this_year": year_new,
            },
        },
    }


def run_category_distribution(db: Session, user_id: int) -> Dict[str, Any]:
    category_counts = (
        db.query(models.ClothingItem.category, func.count(models.ClothingItem.id).label("count"))
        .filter(models.ClothingItem.user_id == user_id)
        .group_by(models.ClothingItem.category)
        .order_by(func.count(models.ClothingItem.id).desc())
        .all()
    )

    category_colors = {
        "top": "#FCD568",
        "bottom": "#68C5FA",
        "dress": "#FF69B4",
        "outerwear": "#A694F5",
        "footwear": "#E57373",
        "accessory": "#4DB6AC",
        "bag": "#FFB347",
        "underwear": "#E0E0E0",
        "other": "#999999",
    }

    category_names = {
        "top": "Tops",
        "bottom": "Bottoms",
        "dress": "Dress",
        "outerwear": "Outerwear",
        "footwear": "Footwear",
        "accessory": "Accessories",
        "bag": "Bag",
        "underwear": "Underwear",
        "other": "Other",
    }

    distribution_data = []
    for cat in category_counts:
        if cat.category:
            distribution_data.append(
                {
                    "label": category_names.get(cat.category, cat.category),
                    "value": cat.count,
                    "color": category_colors.get(cat.category, "#999999"),
                }
            )

    return {"success": True, "data": distribution_data}


def run_export_trend_data(
    db: Session,
    user_id: int,
    format: str,
    view_by: str,
    start_year: Optional[int],
    end_year: Optional[int],
) -> Union[Dict[str, Any], Response]:
    trend_response = run_total_items_trend(
        db,
        user_id,
        view_by,
        start_year,
        end_year,
        include_projection=False,
    )

    if not trend_response.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch trend data")

    trend_data = trend_response["data"]

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Time", "New Items", "Total Items"])
        for i in range(len(trend_data["labels"])):
            writer.writerow(
                [
                    trend_data["labels"][i],
                    trend_data["increments"][i],
                    trend_data["values"][i],
                ]
            )
        filename = f"clothing_trend_{view_by}_{datetime.now().strftime('%Y%m%d')}.csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    return trend_response

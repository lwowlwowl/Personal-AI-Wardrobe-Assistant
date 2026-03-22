"""衣櫥分析 API（路徑與行為與重構前 main 一致）。"""
import csv
import json
import traceback
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import Date, func
from sqlalchemy.orm import Session

import app.crud as crud
import app.models as models
from AIwardrobe.model.factory import chat_model
from AIwardrobe.utils.database_retriever import build_agent_context
from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(tags=["analysis"])


class TrendDataService:
    """衣物趋势数据服务类 - 封装所有趋势相关的业务逻辑"""

    @staticmethod
    def get_date_range(view_by: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """获取时间范围"""
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
            raise ValueError(f"不支持的视图类型: {view_by}")

        return start_date, end_date

    @staticmethod
    def generate_time_labels(view_by: str,
                             start_date: datetime,
                             end_date: datetime) -> List[str]:
        """生成时间标签"""
        labels = []
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
        """
        获取时间分组字段（PostgreSQL专用）
        注意：返回的是字段表达式，不是label
        """
        if view_by == "yearly":
            # 提取年份
            return func.extract('year', models.ClothingItem.created_at)
        elif view_by == "monthly":
            # 格式化为 YYYY-MM
            return func.to_char(models.ClothingItem.created_at, 'YYYY-MM')
        elif view_by == "daily" or view_by == "weekly":
            # 转换为日期
            return func.cast(models.ClothingItem.created_at, Date)
        else:
            return func.extract('year', models.ClothingItem.created_at)


def _build_suggested_additions_context(user_id: int, db: Session) -> dict[str, Any]:
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


def _parse_suggested_additions_content(content: str) -> list[str]:
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
            parsed = json.loads(cleaned[start:end + 1])
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


async def _generate_suggested_additions(prompt_context: dict[str, Any]) -> list[str]:
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
    return _parse_suggested_additions_content(getattr(response, "content", ""))


@router.get("/api/analysis/total-items/trend")
async def get_total_items_trend(
        token: str = Query(...),
        db: Session = Depends(get_db),
        view_by: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
        start_year: Optional[int] = Query(None, ge=2000, le=2100),
        end_year: Optional[int] = Query(None, ge=2000, le=2100),
        include_projection: bool = Query(True, description="是否包含预测数据")
):
    try:
        print(f"===== 收到趋势API请求 =====")
        print(f"view_by: {view_by}")

        current_user = get_current_user(token, db)

        # 初始化趋势数据服务
        trend_service = TrendDataService()

        # 获取用户最早衣物时间
        first_item = db.query(func.min(models.ClothingItem.created_at)).filter(
            models.ClothingItem.user_id == current_user.id,
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
                    "statistics": {}
                }
            }

        now = datetime.now()

        # 确定时间范围
        if view_by == "yearly":
            start_date = datetime(start_year or first_item.year, 1, 1)
            end_date = datetime(end_year or now.year, 12, 31)
        else:
            start_date, end_date = trend_service.get_date_range(view_by)

        # 获取分组字段
        group_field = trend_service.get_time_group_field(view_by)

        # 查询衣物数量（按时间分组）
        # 重要：在 group_by 和 order_by 中使用相同的表达式
        query = db.query(
            group_field.label('time_period'),
            func.count(models.ClothingItem.id).label('increment')
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.created_at.between(start_date, end_date)
        ).group_by(
            group_field  # 使用表达式，而不是label
        ).order_by(
            group_field  # 使用表达式，而不是label
        )

        results = query.all()
        print(f"查询结果: {len(results)} 条记录")

        # 生成完整的时间标签
        labels = trend_service.generate_time_labels(view_by, start_date, end_date)

        # 创建数据映射
        increment_map = {}
        for r in results:
            if view_by == "yearly":
                # extract 返回的是 Decimal，需要转换为整数
                key = str(int(r.time_period))
            elif view_by == "monthly":
                # to_char 返回的是字符串
                key = r.time_period
            else:  # daily / weekly
                # cast to Date 返回的是 date 对象
                key = r.time_period.strftime("%Y-%m-%d") if hasattr(r.time_period, 'strftime') else str(r.time_period)
            increment_map[key] = r.increment

        # 构建增量数据和累计数据
        increments = []
        cumulative_values = []
        total = 0

        # 获取历史累计基数
        base_count = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.created_at < start_date
        ).scalar() or 0
        total = base_count

        for i, label in enumerate(labels):
            if view_by == "yearly":
                key = label
            elif view_by == "monthly":
                key = label
            elif view_by == "weekly":
                key = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            else:  # daily
                # 将 "MM/DD" 格式转换为日期键
                try:
                    month, day = map(int, label.split('/'))
                    year = start_date.year
                    if month == 1 and start_date.month == 12:
                        year = end_date.year
                    date_key = datetime(year, month, day).strftime("%Y-%m-%d")
                    key = date_key
                except Exception:
                    key = label

            increment = increment_map.get(key, 0)
            increments.append(increment)
            total += increment
            cumulative_values.append(total)

        # 计算统计指标
        statistics = {}
        if cumulative_values:
            # 平均增长率
            if len(cumulative_values) > 1:
                growth_rates = []
                for i in range(1, len(cumulative_values)):
                    if cumulative_values[i - 1] > 0:
                        rate = (cumulative_values[i] - cumulative_values[i - 1]) / cumulative_values[i - 1] * 100
                        growth_rates.append(rate)
                statistics['avg_growth'] = round(sum(growth_rates) / len(growth_rates), 2) if growth_rates else 0
            else:
                statistics['avg_growth'] = 0

            # 最大增长
            if increments:
                max_growth = max(increments)
                max_index = increments.index(max_growth)
                statistics['max_growth'] = max_growth
                statistics['max_period'] = labels[max_index] if max_index < len(labels) else None

            # 预测数据
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
                    statistics['projection'] = round(projection)

                    last_year = int(labels[-1]) if labels else now.year
                    statistics['projection_year'] = last_year + 1

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
                    "end": end_date.isoformat() if end_date else None
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取衣物趋势数据错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物趋势数据时发生错误: {str(e)}"
        )


@router.get("/api/analysis/total-items/summary")
async def get_total_items_summary(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物总数概览信息（使用简单查询）
    """
    try:
        current_user = get_current_user(token, db)

        now = datetime.now()

        # 时间范围定义
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # 上月同期
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        # 基础查询
        base_query = db.query(models.ClothingItem).filter(
            models.ClothingItem.user_id == current_user.id,
        )

        # 分别查询各个统计数据
        total_items = base_query.count()
        total_value = db.query(func.sum(models.ClothingItem.price)).filter(
            models.ClothingItem.user_id == current_user.id,
        ).scalar() or 0

        categories_count = db.query(func.count(func.distinct(models.ClothingItem.category))).filter(
            models.ClothingItem.user_id == current_user.id,
        ).scalar() or 0

        # 今日新增
        today_new = base_query.filter(models.ClothingItem.created_at >= today_start).count()

        # 本周新增
        week_new = base_query.filter(models.ClothingItem.created_at >= week_start).count()

        # 本月新增
        month_new = base_query.filter(models.ClothingItem.created_at >= month_start).count()

        # 今年新增
        year_new = base_query.filter(models.ClothingItem.created_at >= year_start).count()

        # 上月新增
        last_month_new = base_query.filter(
            models.ClothingItem.created_at.between(last_month_start, last_month_end)
        ).count()

        # 最近添加的5件衣物
        latest_items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.created_at
        ).filter(
            models.ClothingItem.user_id == current_user.id,
        ).order_by(
            models.ClothingItem.created_at.desc()
        ).limit(5).all()

        # 计算增长率
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
                        "created_at": item.created_at.isoformat()
                    }
                    for item in latest_items
                ],
                "growth_rate": growth_rate,
                "stats_by_period": {
                    "today": today_new,
                    "this_week": week_new,
                    "this_month": month_new,
                    "this_year": year_new
                }
            }
        }

    except Exception as e:
        print(f"获取衣物概览统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物概览统计时发生错误: {str(e)}"
        )


@router.get("/api/analysis/total-items/category-distribution")
async def get_category_distribution(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物分类分布数据（用于圆环图）

    返回数据格式：
    {
        "success": true,
        "data": [
            {"label": "上衣", "value": 35, "color": "#FCD568"},
            ...
        ]
    }
    """
    try:
        current_user = get_current_user(token, db)

        # 查询各分类数量
        from sqlalchemy import func

        category_counts = db.query(
            models.ClothingItem.category,
            func.count(models.ClothingItem.id).label('count')
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).group_by(
            models.ClothingItem.category
        ).order_by(
            func.count(models.ClothingItem.id).desc()
        ).all()

        # 分类颜色映射
        category_colors = {
            "top": "#FCD568",  # 上衣 - 黄色
            "bottom": "#68C5FA",  # 下装 - 蓝色
            "dress": "#FF69B4",  # 连衣裙 - 粉色
            "outerwear": "#A694F5",  # 外套 - 紫色
            "footwear": "#E57373",  # 鞋履 - 红色
            "accessory": "#4DB6AC",  # 配饰 - 青色
            "bag": "#FFB347",       # 包 - 橙色
            "underwear": "#E0E0E0", # 内衣 - 灰色
            "other": "#999999"      # 其他 - 深灰色
        }

        # 分类名称映射（用于显示，英文）
        category_names = {
            "top": "Tops",
            "bottom": "Bottoms",
            "dress": "Dress",
            "outerwear": "Outerwear",
            "footwear": "Footwear",
            "accessory": "Accessories",
            "bag": "Bag",
            "underwear": "Underwear",
            "other": "Other"
        }

        # 构建返回数据
        distribution_data = []
        for cat in category_counts:
            if cat.category:  # 确保分类不为空
                distribution_data.append({
                    "label": category_names.get(cat.category, cat.category),
                    "value": cat.count,
                    "color": category_colors.get(cat.category, "#999999")
                })

        return {
            "success": True,
            "data": distribution_data
        }

    except Exception as e:
        print(f"获取分类分布错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类分布时发生错误: {str(e)}"
        )


@router.get("/api/analysis/total-items/export")
async def export_trend_data(
        token: str = Query(...),
        db: Session = Depends(get_db),
        format: str = Query("json", regex="^(json|csv)$"),
        view_by: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
        start_year: Optional[int] = Query(None),
        end_year: Optional[int] = Query(None)
):
    """
    导出衣物趋势数据
    支持JSON和CSV格式
    """
    try:
        current_user = get_current_user(token, db)

        # 先获取趋势数据
        trend_response = await get_total_items_trend(
            token=token,
            db=db,
            view_by=view_by,
            start_year=start_year,
            end_year=end_year,
            include_projection=False
        )

        if not trend_response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取趋势数据失败"
            )

        trend_data = trend_response["data"]

        if format == "csv":
            # 生成CSV格式
            output = StringIO()
            writer = csv.writer(output)

            # 写入表头
            writer.writerow(["时间", "新增数量", "累计总数"])

            # 写入数据
            for i in range(len(trend_data["labels"])):
                writer.writerow([
                    trend_data["labels"][i],
                    trend_data["increments"][i],
                    trend_data["values"][i]
                ])

            # 返回CSV文件
            filename = f"clothing_trend_{view_by}_{datetime.now().strftime('%Y%m%d')}.csv"
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON格式
            return trend_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"导出趋势数据错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出趋势数据时发生错误: {str(e)}"
        )


@router.get("/api/analysis/idle-rate")
async def get_idle_rate(
        token: str = Query(...),
        db: Session = Depends(get_db),
        days: int = Query(30, ge=1, le=365, description="闲置天数阈值")
):
    """
    获取衣物的闲置率统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
        days: 闲置天数阈值（默认30天未穿视为闲置）
    返回：
        闲置率、闲置数量、总数等信息
    """
    try:
        current_user = get_current_user(token, db)

        # 计算截止日期
        from datetime import datetime, timedelta, date  # 导入 date
        cutoff_date = datetime.now() - timedelta(days=days)
        today = date.today()

        # 1. 获取总衣物数
        total_items = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id
        ).scalar() or 0

        # 2. 获取闲置衣物数（从未穿过或最后穿着时间超过阈值）
        idle_items = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            # 满足以下任一条件视为闲置：
            # 1. wear_count为0（从未穿过）
            # 2. last_worn_date小于截止日期（超过阈值未穿）
            # 3. last_worn_date为null（从未穿过）
            (
                    (models.ClothingItem.wear_count == 0) |
                    (models.ClothingItem.last_worn_date < cutoff_date) |
                    (models.ClothingItem.last_worn_date.is_(None))
            )
        ).scalar() or 0

        # 3. 计算闲置率
        idle_rate = round((idle_items / total_items * 100), 1) if total_items > 0 else 0

        # 4. 获取最久未穿的几件衣物（用于详情页）
        most_idle_items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.wear_count,
            models.ClothingItem.last_worn_date
        ).filter(
            models.ClothingItem.user_id == current_user.id,
        ).order_by(
            # 按最后穿着时间升序（最久未穿的排在前面）
            models.ClothingItem.last_worn_date.asc().nullsfirst()  # null（从未穿过）排在最前
        ).limit(10).all()

        # 构建返回数据
        most_idle_items_data = []
        for item in most_idle_items:
            days_since_last_worn = None
            if item.last_worn_date:
                # 使用 date 对象相减
                days_since_last_worn = (today - item.last_worn_date).days
            else:
                # 从未穿过，给一个较大的值
                days_since_last_worn = days * 2

            most_idle_items_data.append({
                "id": item.id,
                "name": item.name,
                "image_url": item.image_url,
                "wear_count": item.wear_count,
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
                "days_since_last_worn": days_since_last_worn
            })

        return {
            "success": True,
            "data": {
                "total_items": total_items,
                "idle_items": idle_items,
                "idle_rate": idle_rate,
                "threshold_days": days,
                "most_idle_items": most_idle_items_data
            }
        }

    except Exception as e:
        print(f"获取闲置率错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取闲置率时发生错误: {str(e)}"
        )


@router.get("/api/analysis/idle-items/detail")
async def get_idle_items_detail(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        time_filter: Optional[str] = Query(None, regex="^(never|over_season|over_year|over_six_months|over_three_months)$"),
        season_filter: Optional[str] = Query(None)
):
    """
    获取闲置物品详情列表（支持筛选）。
    season 为数组，筛选时用「包含」该季节。
    """
    try:
        current_user = get_current_user(token, db)

        from datetime import datetime, timedelta, date
        now = datetime.now()
        today = date.today()

        query = db.query(models.ClothingItem).filter(
            models.ClothingItem.user_id == current_user.id
        )

        if time_filter is None:
            cutoff_date = today - timedelta(days=30)
            query = query.filter(
                (models.ClothingItem.wear_count == 0) |
                (models.ClothingItem.last_worn_date < cutoff_date) |
                (models.ClothingItem.last_worn_date.is_(None))
            )
        elif time_filter == "never":
            query = query.filter(models.ClothingItem.wear_count == 0)
        elif time_filter == "over_season":
            cutoff = today - timedelta(days=90)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )
        elif time_filter == "over_year":
            cutoff = today - timedelta(days=365)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )
        elif time_filter == "over_six_months":
            cutoff = today - timedelta(days=180)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )
        elif time_filter == "over_three_months":
            cutoff = today - timedelta(days=90)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )

        if season_filter and season_filter != "all":
            try:
                season_enum = models.ClothingSeason(season_filter)
                query = query.filter(models.ClothingItem.season.contains([season_enum]))
            except ValueError:
                pass

        # 分页
        total = query.count()
        skip = (page - 1) * page_size
        rows = query.order_by(
            models.ClothingItem.last_worn_date.asc().nullsfirst()
        ).offset(skip).limit(page_size).all()

        # 序列化为明确 dict，确保前端能拿到 id 等栏位（供 Try today / 日历等使用）
        items = []
        for row in rows:
            season_val = None
            if getattr(row, "season", None) is not None:
                try:
                    season_val = [s.value if hasattr(s, "value") else str(s) for s in row.season]
                except Exception:
                    season_val = []
            items.append({
                "id": row.id,
                "name": row.name,
                "image_url": getattr(row, "image_url", None) or "",
                "wear_count": getattr(row, "wear_count", 0) or 0,
                "last_worn_date": row.last_worn_date.isoformat() if getattr(row, "last_worn_date", None) else None,
                "season": season_val,
                "category": getattr(row, "category", None).value if getattr(row, "category", None) is not None and hasattr(row.category, "value") else None,
                "color": getattr(row, "color", None),
                "color_code": getattr(row, "color_code", None),
            })

        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }

    except Exception as e:
        print(f"获取闲置物品详情错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取闲置物品详情时发生错误: {str(e)}"
        )


@router.get("/api/analysis/top-color")
async def get_top_color(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户衣柜中最常用的颜色统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        最常用颜色及其占比
    """
    try:
        current_user = get_current_user(token, db)

        # 查询用户所有衣物的颜色分布
        color_counts = db.query(
            models.ClothingItem.color,
            func.count(models.ClothingItem.id).label('count')
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.color.isnot(None)  # 排除颜色为空的记录
        ).group_by(
            models.ClothingItem.color
        ).order_by(
            func.count(models.ClothingItem.id).desc()
        ).all()

        # 计算总数
        total_items_with_color = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.color.isnot(None)
        ).scalar() or 0

        # 颜色名称映射（API 返回英文，供前端展示）
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
            "multicolor": "Multicolor"
        }

        # 构建返回数据
        top_color_data = []
        for color_item in color_counts:
            top_color_data.append({
                "color_code": color_item.color,
                "color_name": color_name_map.get(color_item.color, color_item.color),
                "count": color_item.count,
                "percentage": round((color_item.count / total_items_with_color * 100),
                                    1) if total_items_with_color > 0 else 0
            })

        # 获取最常用颜色
        top_color = top_color_data[0] if top_color_data else {
            "color_code": "brown",
            "color_name": "Brown",
            "count": 0,
            "percentage": 0
        }

        return {
            "success": True,
            "data": {
                "top_color": top_color,
                "color_distribution": top_color_data,
                "total_items_with_color": total_items_with_color
            }
        }

    except Exception as e:
        print(f"获取颜色统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取颜色统计时发生错误: {str(e)}"
        )


@router.get("/api/analysis/top-style")
async def get_top_style(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户衣柜中最常用的风格统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        最常用风格及其占比
    """
    try:
        current_user = get_current_user(token, db)

        # 通过标签统计风格（假设风格以标签形式存储）
        style_tags = db.query(
            models.ClothingTag.tag,
            func.count(models.ClothingTag.id).label('count')
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingTag.tag.in_([
                "sporty", "casual", "formal", "business",
                "minimal", "bohemian", "vintage", "streetwear",
                "运动", "休闲", "正式", "商务", "简约", "波西米亚", "复古", "街头"
            ])
        ).group_by(
            models.ClothingTag.tag
        ).order_by(
            func.count(models.ClothingTag.id).desc()
        ).all()

        # 风格名称映射（API 返回英文）
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
            "街头": "Streetwear"
        }

        # 计算总数
        total_styles = sum(item.count for item in style_tags) or 1

        # 构建返回数据
        style_data = []
        for style_item in style_tags:
            style_data.append({
                "style_code": style_item.tag,
                "style_name": style_name_map.get(style_item.tag, style_item.tag),
                "count": style_item.count,
                "percentage": round((style_item.count / total_styles * 100), 1)
            })

        # 获取最常用风格
        top_style = style_data[0] if style_data else {
            "style_code": "casual",
            "style_name": "Casual",
            "count": 0,
            "percentage": 0
        }

        return {
            "success": True,
            "data": {
                "top_style": top_style,
                "style_distribution": style_data,
                "total_styles_count": total_styles
            }
        }

    except Exception as e:
        print(f"获取风格统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取风格统计时发生错误: {str(e)}"
        )


@router.get("/api/analysis/most-worn")
async def get_most_worn_items(
        token: str = Query(...),
        db: Session = Depends(get_db),
        time_range: str = Query("yearly", regex="^(yearly|monthly|daily|weekly)$"),
        limit: int = Query(5, ge=1, le=20, description="返回数量")
):
    """
    获取最常穿物品（支持时间范围筛选）
    """
    try:
        print(f"========== 收到最常穿物品请求 ==========")
        print(f"time_range: {time_range}")
        print(f"limit: {limit}")

        current_user = get_current_user(token, db)
        print(f"用户ID: {current_user.id}")

        from datetime import datetime, date, timedelta

        now = datetime.now()
        today = date.today()

        # 根据时间范围设置起始日期
        if time_range == "yearly":
            # 年度统计：从今年1月1日开始
            start_date = date(now.year, 1, 1)
            date_range_text = f"今年 ({now.year}年)"
        elif time_range == "monthly":
            # 月度统计：从本月1日开始
            start_date = date(now.year, now.month, 1)
            date_range_text = f"本月 ({now.year}年{now.month}月)"
        elif time_range == "weekly":
            # 近 7 天（与前端 ViewByFilter「Weekly」一致）
            start_date = today - timedelta(days=7)
            date_range_text = f"近7天 ({start_date.isoformat()} 起)"
        else:  # daily
            # 每日统计：从今天开始
            start_date = today
            date_range_text = f"今天 ({today.isoformat()})"

        print(f"统计起始日期: {start_date} ({date_range_text})")

        # 查询用户的所有衣物
        items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.color,
            models.ClothingItem.wear_count,
            models.ClothingItem.last_worn_date,
            models.ClothingItem.created_at
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).all()

        print(f"找到 {len(items)} 件衣物")

        # 如果没有衣物数据，返回空列表
        if not items:
            return {
                "success": True,
                "data": {
                    "items": [],
                    "time_range": time_range,
                    "date_range": date_range_text
                }
            }

        # 构建返回数据，计算在时间范围内的穿着次数
        most_worn_data = []

        for item in items:
            # 基础信息
            item_data = {
                "id": item.id,
                "name": item.name,
                "color": item.color or "gray",
                "total_wear_count": item.wear_count,  # 总穿着次数
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
            }

            # 计算在指定时间范围内的穿着次数
            wears_in_range = 0

            if item.last_worn_date:
                # 转换 last_worn_date 为 date 类型
                last_worn = item.last_worn_date
                if hasattr(last_worn, 'date'):
                    last_worn = last_worn.date()

                # 如果在时间范围内有穿着记录
                if last_worn >= start_date:
                    # 对于 yearly/monthly/weekly/daily 的不同处理
                    if time_range == "daily":
                        # 每日：如果最后穿着时间是今天，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn == today else 0
                    elif time_range == "weekly":
                        # 近7天：最后穿着落在窗口内则沿用与 monthly 相同的「总次数」近似（非逐日 wear_history）
                        wears_in_range = item.wear_count
                    elif time_range == "monthly":
                        # 月度：如果最后穿着时间在本月，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn.month == now.month and last_worn.year == now.year else 0
                    else:  # yearly
                        # 年度：如果最后穿着时间在今年，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn.year == now.year else 0
                else:
                    wears_in_range = 0
            else:
                # 从未穿过
                wears_in_range = 0

            item_data["wear_count"] = wears_in_range  # 时间范围内的穿着次数

            # 添加调试信息
            print(
                f"衣物: {item.name}, 总穿着: {item.wear_count}, 最后穿着: {item.last_worn_date}, 范围内穿着: {wears_in_range}, 时间范围: {time_range}")

            most_worn_data.append(item_data)

        # 按穿着次数排序并限制数量
        most_worn_data.sort(key=lambda x: x["wear_count"], reverse=True)
        most_worn_data = most_worn_data[:limit]

        # 格式化返回数据（保持与前端期望的格式一致）
        formatted_items = [
            {
                "name": item["name"],
                "wears": item["wear_count"],
                "color": item["color"]
            }
            for item in most_worn_data
        ]

        print(f"返回数据: {formatted_items}")

        return {
            "success": True,
            "data": {
                "items": formatted_items,
                "time_range": time_range,
                "date_range": date_range_text,
                "total_items": len(items)
            }
        }

    except Exception as e:
        print(f"获取最常穿物品错误: {traceback.format_exc()}")
        # 出错时返回模拟数据，避免前端崩溃
        return {
            "success": True,
            "data": {
                "items": [
                    {"name": "示例物品1", "wears": 10, "color": "blue"},
                    {"name": "示例物品2", "wears": 8, "color": "black"},
                    {"name": "示例物品3", "wears": 5, "color": "white"},
                ],
                "time_range": time_range,
                "note": "返回了示例数据（后端出错）"
            }
        }


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


@router.get("/api/analysis/weekly-activity")
async def get_weekly_activity(
        token: str = Query(...),
        db: Session = Depends(get_db),
):
    """
    本周衣橱活跃度：总穿戴次数、环比上周趋势、每日穿戴分布、按分类统计。
    用于主面板 Wardrobe Activity 卡片与展开页 Activity Report。
    """
    try:
        current_user = get_current_user(token, db)
        today = date.today()
        # 本周一与本周日（周一为 week 起点）
        this_week_monday = today - timedelta(days=today.weekday())
        this_week_sunday = this_week_monday + timedelta(days=6)
        last_week_monday = this_week_monday - timedelta(days=7)
        last_week_sunday = this_week_sunday - timedelta(days=7)

        # 本周总穿戴次数：WearHistory 中 wear_date 在本周且 clothing_id 非空（单件穿着记录）
        q_this_week = db.query(func.count(models.WearHistory.id)).filter(
            models.WearHistory.user_id == current_user.id,
            models.WearHistory.wear_date >= this_week_monday,
            models.WearHistory.wear_date <= this_week_sunday,
            models.WearHistory.clothing_id.isnot(None),
        )
        total_wears_this_week = q_this_week.scalar() or 0

        q_last_week = db.query(func.count(models.WearHistory.id)).filter(
            models.WearHistory.user_id == current_user.id,
            models.WearHistory.wear_date >= last_week_monday,
            models.WearHistory.wear_date <= last_week_sunday,
            models.WearHistory.clothing_id.isnot(None),
        )
        total_wears_last_week = q_last_week.scalar() or 0

        # 趋势百分比：(本期 - 上期) / 上期 * 100，上期为 0 时按 0 处理
        if total_wears_last_week > 0:
            trend_percent = round(
                (total_wears_this_week - total_wears_last_week) / total_wears_last_week * 100
            )
        else:
            trend_percent = 0 if total_wears_this_week == 0 else 100

        # 每日穿戴次数：按 wear_date 分组统计本周
        daily_counts = (
            db.query(models.WearHistory.wear_date, func.count(models.WearHistory.id).label("cnt"))
            .filter(
                models.WearHistory.user_id == current_user.id,
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

        # 按分类统计本周穿戴次数：WearHistory join ClothingItem，按 category 聚合
        category_rows = (
            db.query(models.ClothingItem.category, func.count(models.WearHistory.id).label("cnt"))
            .join(models.WearHistory, models.WearHistory.clothing_id == models.ClothingItem.id)
            .filter(
                models.WearHistory.user_id == current_user.id,
                models.WearHistory.wear_date >= this_week_monday,
                models.WearHistory.wear_date <= this_week_sunday,
            )
            .group_by(models.ClothingItem.category)
            .all()
        )
        category_map_agg = {}
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取本周活跃度错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取本周活跃度时发生错误: {str(e)}"
        )


@router.get("/api/analysis/suggested-additions")
async def get_suggested_additions(
        token: str = Query(...),
        db: Session = Depends(get_db),
        limit: int = Query(3, ge=1, le=3, description="固定返回 3 条建议")
):
    """
    基于用户现有衣橱，返回 3 条纯文本建议新增项。
    触发时机：前端进入 Wardrobe Analysis 且用户已登录时调用。
    """
    try:
        current_user = get_current_user(token, db)
        prompt_context = _build_suggested_additions_context(current_user.id, db)
        closet_count = prompt_context.get("summary", {}).get("counts", {}).get("closet_items", 0)

        if not closet_count:
            items = []
        else:
            items = await _generate_suggested_additions(prompt_context)

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
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取推荐添加错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推荐添加时发生错误: {str(e)}"
        )


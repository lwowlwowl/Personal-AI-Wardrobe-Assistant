"""日曆穿搭 API（路徑與行為與重構前 main 一致）。"""
import calendar
import traceback
from datetime import date, datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter(tags=["calendar"])


# ============ 日历穿搭记录 API ============


@router.get("/api/calendar/outfits")
async def get_calendar_outfits(
        token: str = Query(..., description="用户认证令牌"),
        year: int = Query(..., description="年份，例如 2025"),
        month: int = Query(..., ge=1, le=12, description="月份，1-12")
        , db: Session = Depends(get_db)
):
    """
    获取指定月份的穿搭记录（供 MyCalendar 使用）
    响应结构遵循 MY_CALENDAR.md：
    {
      success: true,
      message: "Success",
      data: { outfits: { "YYYY-MM-DD": [items] } },
      status_code: 200
    }
    """
    try:
        current_user = get_current_user(token, db)

        try:
            # 计算当月第一天和最后一天
            first_day = date(year, month, 1)
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = date(year, month, last_day_num)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid year or month.",
            )

        # 查询当前用户在该月份的穿着记录（按衣物维度）
        # 仅统计有 clothing_id 的记录，忽略 outfit_id 为主的记录
        histories = (
            db.query(models.WearHistory, models.ClothingItem)
            .join(models.ClothingItem, models.WearHistory.clothing_id == models.ClothingItem.id)
            .filter(
                models.WearHistory.user_id == current_user.id,
                models.WearHistory.wear_date >= first_day,
                models.WearHistory.wear_date <= last_day,
                models.WearHistory.clothing_id.isnot(None)
            )
            .all()
        )

        outfits: Dict[str, List[Dict[str, Any]]] = {}
        unique_ids: set = set()

        for history, clothing in histories:
            date_key = history.wear_date.strftime("%Y-%m-%d")
            image_url = clothing.image_url or ""
            item = {
                "id": clothing.id,
                "name": clothing.name,
                # 前端会按需补全为完整 URL，这里只返回后端存储的路径
                "image": image_url,
                # 可选字段：目前直接复用 clothing.color（如有需要前端可转为 accentColor）
                "accentColor": None,
            }
            outfits.setdefault(date_key, []).append(item)
            if clothing.id is not None:
                unique_ids.add(clothing.id)

        # 统计字段（可选，前端也会自行计算）
        days_recorded = sum(1 for items in outfits.values() if items)

        data = {
            "outfits": outfits,
            "monthStats": {
                "daysRecorded": days_recorded,
                "uniqueItems": len(unique_ids),
            },
        }

        return {
            "success": True,
            "message": "Success",
            "data": data,
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception:
        print(f"获取日历穿搭记录错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while loading the calendar.",
        )


@router.post("/api/calendar/outfits")
async def save_calendar_outfits(
        payload: schemas.CalendarOutfitSave,
        token: str = Query(..., description="用户认证令牌"),
        db: Session = Depends(get_db)
):
    """
    保存 / 更新 / 删除某天的穿搭记录（全量覆盖）
    - items 为空数组表示删除该日期记录
    """
    try:
        current_user = get_current_user(token, db)

        # 校验日期
        try:
            wear_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date must be YYYY-MM-DD.",
            )

        # 校验 items
        if payload.items is None or not isinstance(payload.items, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field 'items' must be an array.",
            )

        clothing_ids = [item.id for item in payload.items if item.id is not None]
        if len(clothing_ids) != len(payload.items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each item must include a clothing id.",
            )

        # 校验衣物归属
        if clothing_ids:
            clothing_list = db.query(models.ClothingItem).filter(
                models.ClothingItem.user_id == current_user.id,
                models.ClothingItem.id.in_(clothing_ids)
            ).all()
            owned_ids = {c.id for c in clothing_list}
            missing_ids = [cid for cid in clothing_ids if cid not in owned_ids]
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more items are not in your wardrobe.",
                )

        # 获取当前日期已存在的穿着记录（仅 clothing_id 维度）
        existing_histories = db.query(models.WearHistory).filter(
            models.WearHistory.user_id == current_user.id,
            models.WearHistory.wear_date == wear_date,
            models.WearHistory.clothing_id.isnot(None),
            models.WearHistory.outfit_id.is_(None),
        ).all()

        existing_by_clothing = {
            h.clothing_id: h for h in existing_histories if h.clothing_id is not None
        }
        new_id_set = set(clothing_ids)

        # 1）删除不再包含的记录，并重算被删衣物的「最后穿上」与穿着次数
        removed_cids = [cid for cid in existing_by_clothing if cid not in new_id_set]
        for cid in removed_cids:
            db.delete(existing_by_clothing[cid])
        if removed_cids:
            db.flush()
            crud.WearHistoryCRUD.recompute_clothing_after_removal(db, current_user.id, removed_cids)

        # 2）新增新的记录（使用 WearHistoryCRUD，保证 wear_count 等统计更新）
        for cid in new_id_set:
            if cid not in existing_by_clothing:
                history_in = schemas.WearHistoryCreate(
                    wear_date=wear_date,
                    clothing_id=cid,
                    outfit_id=None,
                    weather=None,
                    temperature=None,
                    location=None,
                    occasion=None,
                    notes=None,
                    rating=None,
                )
                _, error = crud.WearHistoryCRUD.create_wear_history(
                    db=db,
                    user_id=current_user.id,
                    history_in=history_in,
                )
                if error:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error
                    )

        db.commit()

        # 重新查询该日期的记录并按前端需要的结构返回
        refreshed = (
            db.query(models.WearHistory, models.ClothingItem)
            .join(models.ClothingItem, models.WearHistory.clothing_id == models.ClothingItem.id)
            .filter(
                models.WearHistory.user_id == current_user.id,
                models.WearHistory.wear_date == wear_date,
                models.WearHistory.clothing_id.isnot(None),
            )
            .all()
        )

        items: List[Dict[str, Any]] = []
        for history, clothing in refreshed:
            image_url = clothing.image_url or ""
            items.append({
                "id": clothing.id,
                "name": clothing.name,
                "image": image_url,
                "accentColor": None,
            })

        message = "Deleted" if not items else "Saved"

        return {
            "success": True,
            "message": message,
            "data": {
                "date": wear_date.strftime("%Y-%m-%d"),
                "items": items,
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except ValidationError as e:
        # 如 wear_date 为未来日期等 Pydantic 校验错误，返回 400；去掉 "Value error, " 等前缀，只给用户看人话
        try:
            msg_list = [err.get("msg", "") for err in e.errors()]  # type: ignore[attr-defined]
            raw = "; ".join([m for m in msg_list if m]) or "Invalid request data."
            s = raw.strip()
            if s.lower().startswith("value error"):
                rest = s[11:].lstrip(" ,，:：")
                detail = rest if rest else "Invalid request data."
            else:
                detail = s or "Invalid request data."
        except Exception:
            detail = "Invalid request data."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    except Exception:
        db.rollback()
        print(f"保存日历穿搭记录错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while loading the calendar.",
        )


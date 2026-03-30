"""Calendar outfit APIs (paths and behavior match pre-refactor main)."""
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


# ============ Calendar outfit records ============


@router.get("/api/calendar/outfits")
async def get_calendar_outfits(
        token: str = Query(..., description="Auth token"),
        year: int = Query(..., description="Year, e.g. 2025"),
        month: int = Query(..., ge=1, le=12, description="Month, 1-12"),
        db: Session = Depends(get_db),
):
    """
    Month view of wear records for MyCalendar.

    Response shape per src/docs/api/my_calendar_api.md:
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
            first_day = date(year, month, 1)
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = date(year, month, last_day_num)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid year or month.",
            )

        # Wear rows for the month (clothing_id only; ignore outfit-only rows)
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
                # Client may resolve to full URL; we return stored path
                "image": image_url,
                # Optional: maps from clothing.color to accentColor on client if needed
                "accentColor": None,
            }
            outfits.setdefault(date_key, []).append(item)
            if clothing.id is not None:
                unique_ids.add(clothing.id)

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
        print(f"calendar outfits get error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while loading the calendar.",
        )


@router.post("/api/calendar/outfits")
async def save_calendar_outfits(
        payload: schemas.CalendarOutfitSave,
        token: str = Query(..., description="Auth token"),
        db: Session = Depends(get_db)
):
    """
    Save / update / clear a day's outfits (full replace for that date).
    Empty items array removes all records for that date.
    """
    try:
        current_user = get_current_user(token, db)

        try:
            wear_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date must be YYYY-MM-DD.",
            )

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

        # Remove rows no longer in payload; recompute wear stats for removed items
        removed_cids = [cid for cid in existing_by_clothing if cid not in new_id_set]
        for cid in removed_cids:
            db.delete(existing_by_clothing[cid])
        if removed_cids:
            db.flush()
            crud.WearHistoryCRUD.recompute_clothing_after_removal(db, current_user.id, removed_cids)

        # Insert new rows via CRUD so wear_count stays consistent
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
        # Pydantic errors (e.g. future wear_date): strip "Value error, " prefix for clients
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
        print(f"calendar outfits save error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while loading the calendar.",
        )

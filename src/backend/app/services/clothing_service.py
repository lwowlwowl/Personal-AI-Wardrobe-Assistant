"""
衣物業務編排（與路由 HTTP 路徑無關）；upload 等重邏輯從 api/v1/clothing 遷入。
"""
from __future__ import annotations

import json
import traceback
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

import app.crud as crud
import app.models as models
import app.schemas as schemas
from AIwardrobe.agent.classify_model import ClassificationModel
from app.services.file_service import (
    UPLOAD_DIR,
    UPLOAD_URL_PREFIX,
    delete_file,
    save_upload_file,
)


def parse_season_form(season: Optional[str], allow_empty: bool = False) -> Optional[List[str]]:
    if not season:
        return None
    return json.loads(season)


def normalize_category(category: Optional[str]) -> str:
    """
    将传入的 category 规范为后端 ClothingCategory 枚举值字符串。
    - 空值 → "other"
    - 非法值 → "other"
    - 合法值：top/bottom/dress/outerwear/footwear/accessory/bag/underwear/other
    """
    if not category or not category.strip():
        return "other"
    key = category.strip().lower()
    allowed = {c.value for c in models.ClothingCategory}
    return key if key in allowed else "other"


def run_upload_clothing_item(
    *,
    db: Session,
    user: models.User,
    file: UploadFile,
    name: Optional[str],
    category: Optional[str],
    subcategory: Optional[str],
    style: Optional[str],
    color: Optional[str],
    season: Optional[str],
    color_code: Optional[str],
    pattern: Optional[str],
    occasion: Optional[str],
    brand: Optional[str],
    tags: Optional[str],
    description: Optional[str],
    price: Optional[float],
    purchase_date: Optional[str],
    auto_label: bool,
) -> dict:
    """上傳衣物圖片並建立記錄；行為與原 clothing.upload_clothing_item 一致。"""
    try:
        image_url = save_upload_file(file, user.id)
        relative_path = image_url[len(UPLOAD_URL_PREFIX) + 1 :]
        local_image_path = (UPLOAD_DIR / relative_path).resolve()

        tag_list: List[str] = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        season_list = parse_season_form(season, allow_empty=False) if season is not None else None

        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = date.fromisoformat(purchase_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid purchase date format. Use YYYY-MM-DD.",
                )

        label_result: Optional[Dict[str, Any]] = None
        if auto_label:
            try:
                raw_result = ClassificationModel().execute(path=str(local_image_path))
                parsed = json.loads(raw_result.strip())

                label_result = {}
                for field in (
                    "category",
                    "subcategory",
                    "style",
                    "color",
                    "color_code",
                    "pattern",
                    "occasion",
                    "description",
                ):
                    value = parsed.get(field)
                    if value is not None and str(value).strip() != "":
                        label_result[field] = str(value).strip()

                if parsed.get("season"):
                    label_result["season"] = parsed.get("season")
                label_result["_raw"] = parsed
            except Exception as e:
                if not category:
                    delete_file(image_url)
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Automatic image labeling failed: {str(e)}",
                    )

        resolved: Dict[str, Any] = {
            "name": name,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "style": style,
            "color": color,
            "color_code": color_code,
            "pattern": pattern,
            "season": season_list,
            "occasion": occasion,
            "brand": brand,
            "price": price,
            "purchase_date": purchase_date_obj,
            "tags": tag_list,
        }

        if label_result:
            for field in (
                "category",
                "subcategory",
                "style",
                "color",
                "color_code",
                "pattern",
                "occasion",
                "description",
            ):
                if not resolved.get(field) and label_result.get(field):
                    resolved[field] = label_result[field]
            if resolved["season"] is None and label_result.get("season"):
                resolved["season"] = label_result["season"]

            if not resolved["tags"]:
                ai_tags = []
                for tag_field in ("subcategory", "style", "occasion", "pattern"):
                    val = label_result.get(tag_field)
                    if val:
                        ai_tags.append(str(val))
                resolved["tags"] = ai_tags

        if not resolved["category"]:
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing category, and auto-labeling did not return a usable category",
            )
        resolved["category"] = normalize_category(resolved["category"])
        if not resolved["name"]:
            fallback_name = resolved.get("subcategory") or resolved["category"]
            resolved["name"] = str(fallback_name)

        item_in = schemas.ClothingItemCreate(**resolved)

        clothing_item, error = crud.clothing_crud.create_clothing_item(
            db=db,
            user_id=user.id,
            item_in=item_in,
            image_url=image_url,
            thumbnail_url=None,
        )

        if error:
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
            )

        return {
            "success": True,
            "message": "Clothing item uploaded successfully.",
            "data": {
                "id": clothing_item.id,
                "name": clothing_item.name,
                "image_url": clothing_item.image_url,
                "created_at": clothing_item.created_at.isoformat(),
                "auto_label": label_result["_raw"] if label_result else None,
                "tags": resolved.get("tags") or [],
            },
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"run_upload_clothing_item error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred while uploading clothing item: {str(e)}",
        )

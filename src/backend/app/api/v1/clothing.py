"""Clothing APIs (paths and behavior match the pre-refactor main module)."""
import traceback
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

import app.crud as crud
import app.models as models
import app.schemas as schemas
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.clothing_service import (
    normalize_category,
    parse_season_form,
    run_upload_clothing_item,
)
from app.services.file_service import delete_file, save_upload_file

router = APIRouter(tags=["clothing"])


# ============ Clothing management ============
@router.post("/api/clothing/upload")
async def upload_clothing_item(
        file: UploadFile = File(...),
        name: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        subcategory: Optional[str] = Form(None),
        style: Optional[str] = Form(None),
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        color_code: Optional[str] = Form(None),
        pattern: Optional[str] = Form(None),
        occasion: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),  # comma-separated tags
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        auto_label: bool = Form(True),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Upload a clothing image and create a database row.

    Args:
        file: image file (required).
        name: item name (optional).
        category: primary category (optional).
        subcategory: free-text subcategory (optional).
        style: style hint (optional).
        color: color label (optional).
        season: season(s) (optional; parsed by the service).
        color_code: hex color, e.g. #RRGGBB (optional).
        pattern: pattern enum string (optional).
        occasion: occasion (optional).
        brand: brand (optional).
        tags: comma-separated tags (optional).
        description: description (optional).
        price: price (optional).
        purchase_date: purchase date as YYYY-MM-DD (optional).
        auto_label: whether to run auto labelling (default True).
        token: auth token.
        db: DB session.

    Returns:
        Created item payload (success + data).
    """
    current_user = get_current_user(token, db)
    return run_upload_clothing_item(
        db=db,
        user=current_user,
        file=file,
        name=name,
        category=category,
        subcategory=subcategory,
        style=style,
        color=color,
        season=season,
        color_code=color_code,
        pattern=pattern,
        occasion=occasion,
        brand=brand,
        tags=tags,
        description=description,
        price=price,
        purchase_date=purchase_date,
        auto_label=auto_label,
    )


@router.get("/api/clothing")
async def get_clothing_items(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Page size"),
        category: Optional[str] = Query(None, description="Filter by category"),
        season: Optional[str] = Query(None, description="Filter by season"),
        color: Optional[str] = Query(None, description="Filter by color"),
        brand: Optional[str] = Query(None, description="Filter by brand"),
        is_favorite: Optional[str] = Query(None, description="Favorite levels, comma-separated e.g. 0,1,2"),
        min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
        max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
        search: Optional[str] = Query(None, description="Search query"),
        order_by: str = Query("created_at", description="Sort field"),
        order_desc: bool = Query(True, description="Sort descending")
):
    """
    List the current user's clothing with pagination, filters, and search.

    Args:
        token: auth token.
        db: DB session.
        page: page index (1-based).
        page_size: page size (max 100).
        category: filter by primary category.
        season: filter by season.
        color: filter by color.
        brand: filter by brand.
        is_favorite: filter by favorite level(s); comma-separated, e.g. "0,1,2".
        min_price: minimum price.
        max_price: maximum price.
        search: fuzzy match on name and description.
        order_by: sort field.
        order_desc: sort descending when True.

    Returns:
        Paginated list payload (items + pagination).
    """
    try:
        current_user = get_current_user(token, db)

        # Parse is_favorite: supports "0,1,2" or a single value.
        is_favorite_parsed = None
        if is_favorite:
            try:
                levels = [int(x.strip()) for x in is_favorite.split(",") if x.strip()]
                levels = [x for x in levels if 0 <= x <= 3]
                if levels:
                    is_favorite_parsed = levels
            except ValueError:
                pass

        skip = (page - 1) * page_size  # offset for SQL LIMIT/OFFSET

        items, total = crud.clothing_crud.get_clothing_items(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            category=category,
            season=season,
            color=color,
            brand=brand,
            is_favorite=is_favorite_parsed,
            min_price=min_price,
            max_price=max_price,
            search=search,
            order_by=order_by,
            order_desc=order_desc
        )

        total_pages = (total + page_size - 1) // page_size  # ceiling division

        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }

    except Exception as e:
        print(f"clothing list error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load clothing list: {str(e)}"
        )


@router.put("/api/clothing/{clothing_id}")
async def update_clothing_item(
        clothing_id: int = Path(..., ge=1, description="Clothing item id"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        name: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        subcategory: Optional[str] = Form(None),
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        is_favorite: Optional[str] = Form(None),
        condition: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    Update one clothing item (partial form fields).

    Args:
        clothing_id: id of the item to update.
        token: auth token.
        db: DB session.
        name: new name (optional).
        category: new primary category, one of nine enum values (optional).
        subcategory: new subcategory, user-defined text (optional).
        color: new color (optional).
        season: new season(s) (optional).
        brand: new brand (optional).
        tags: new tags, comma-separated (optional).
        description: new description (optional).
        price: new price (optional).
        purchase_date: new purchase date YYYY-MM-DD (optional).
        is_favorite: favorite level 0–3 as a string (optional).
        condition: wear condition enum (optional).
        file: new image file; replaces stored image when provided (optional).

    Returns:
        Updated item in `data`.
    """
    try:
        current_user = get_current_user(token, db)

        # Load row and enforce ownership
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or access denied."
            )

        # Replace image when a new file is uploaded
        image_url = item.image_url
        if file:
            delete_file(item.image_url)
            image_url = save_upload_file(file, current_user.id)

        # Split tag string into a list
        tag_list = None
        if tags is not None:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        season_list = parse_season_form(season, allow_empty=True) if season is not None else None

        # is_favorite: integer 0–3
        is_favorite_val = None
        if is_favorite is not None and is_favorite.strip():
            try:
                v = int(is_favorite.strip())
                if 0 <= v <= 3:
                    is_favorite_val = v
            except ValueError:
                pass

        # Parse purchase_date string to date
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = date.fromisoformat(purchase_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid purchase date. Use YYYY-MM-DD."
                )

        # Build Pydantic update payload
        update_data = schemas.ClothingItemUpdate(
            name=name,
            description=description,
            category=normalize_category(category) if category is not None else None,
            subcategory=subcategory,
            color=color,
            season=season_list,
            brand=brand,
            price=price,
            purchase_date=purchase_date_obj,
            is_favorite=is_favorite_val,
            condition=condition,
            tags=tag_list
        )

        updated_item, error = crud.clothing_crud.update_clothing_item(
            db=db,
            db_item=item,
            item_in=update_data
        )

        if error:
            # Roll back newly uploaded file if update failed
            if file:
                delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "Item updated.",
            "data": updated_item
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing update error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update item: {str(e)}"
        )


@router.delete("/api/clothing/{clothing_id}")
async def delete_clothing_item(
        clothing_id: int = Path(..., ge=1, description="Clothing item id"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Delete one clothing item.

    Args:
        clothing_id: id to delete.
        token: auth token.
        db: DB session.

    Returns:
        Success message payload.
    """
    try:
        current_user = get_current_user(token, db)

        # Load row (also need paths for file cleanup)
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or access denied."
            )

        # Delete DB row (cascades tags, etc.)
        success, error = crud.clothing_crud.delete_clothing_item(
            db=db,
            clothing_id=clothing_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Remove image files from storage
        delete_file(item.image_url)
        if item.thumbnail_url:
            delete_file(item.thumbnail_url)

        return {
            "success": True,
            "message": "Item deleted."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing delete error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete item: {str(e)}"
        )


# ============ Bulk operations ============

@router.post("/api/clothing/batch/delete")
async def batch_delete_clothing(
        clothing_ids: List[int],
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Delete multiple clothing items in one request.

    Args:
        clothing_ids: list of item ids to delete.
        token: auth token.
        db: DB session.

    Returns:
        Result payload with deleted count.
    """
    try:
        current_user = get_current_user(token, db)

        if not clothing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select at least one item to delete."
            )

        # Rows to remove files for after DB delete
        items = db.query(models.ClothingItem).filter(
            models.ClothingItem.id.in_(clothing_ids),
            models.ClothingItem.user_id == current_user.id
        ).all()

        # Every id must exist and belong to the user
        if len(items) != len(clothing_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some items were not found or access was denied."
            )

        deleted_count, error = crud.batch_crud.batch_delete_clothing(
            db=db,
            user_id=current_user.id,
            clothing_ids=clothing_ids
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Remove stored images for deleted rows
        for item in items:
            delete_file(item.image_url)
            if item.thumbnail_url:
                delete_file(item.thumbnail_url)

        return {
            "success": True,
            "message": f"Deleted {deleted_count} item(s)."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing batch/delete error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk delete failed: {str(e)}"
        )


@router.post("/api/clothing/batch/update")
async def batch_update_clothing(
        clothing_ids: List[int],
        update_data: Dict[str, Any],
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Update the same fields on many clothing items.

    Args:
        clothing_ids: list of item ids to update.
        update_data: dict of field names to new values.
        token: auth token.
        db: DB session.

    Returns:
        Result payload with updated count.
    """
    try:
        current_user = get_current_user(token, db)

        if not clothing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select at least one item to update."
            )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide fields to update."
            )

        # Apply the same field map to all ids
        updated_count, error = crud.batch_crud.batch_update_clothing(
            db=db,
            user_id=current_user.id,
            clothing_ids=clothing_ids,
            update_data=update_data
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": f"Updated {updated_count} item(s)."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing batch/update error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk update failed: {str(e)}"
        )


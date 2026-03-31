"""Model photo HTTP API (paths and behavior match the pre-refactor main module)."""
import traceback
from pathlib import Path as PathLib
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile, status
from sqlalchemy.orm import Session

import app.crud as crud
from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.file_service import delete_file, save_upload_file

router = APIRouter(tags=["model_photos"])


# ============ Model photo routes ============

@router.post("/api/model-photos/upload")
async def upload_model_photo(
        file: UploadFile = File(...),
        photo_name: str = Form(...),
        description: Optional[str] = Form(None),
        is_primary: Optional[str] = Form("false"),
        is_favorite: Optional[int] = Form(0),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Upload a model photo (for virtual try-on).

    Args:
        file: image file.
        photo_name: display name.
        description: optional text.
        is_primary: form field is the string "true"/"false"; must be parsed to bool
            (in Python ``bool("false")`` is True, so never use bool() on the raw string).
        is_favorite: favorite level 0-3.
        token: auth token.
        db: DB session.

    Returns:
        Success payload with the created model photo in ``data``.
    """
    try:
        # Form sends is_primary as "true"/"false"; bool("false") is True in Python — parse explicitly.
        is_primary_bool = str(is_primary).strip().lower() in ("true", "1", "on", "yes") if is_primary else False
        is_favorite_val = max(0, min(3, int(is_favorite or 0)))

        current_user = get_current_user(token, db)

        # Persist file (shared upload helper with clothing uploads).
        image_url = save_upload_file(file, current_user.id)

        file_size = file.size
        file_ext = PathLib(file.filename).suffix.lower()
        file_format = file_ext[1:] if file_ext else None

        model_photo, error = crud.model_photo_crud.create_model_photo(
            db=db,
            user_id=current_user.id,
            photo_name=photo_name,
            image_url=image_url,
            description=description,
            file_size=file_size,
            file_format=file_format,
            is_primary=is_primary_bool,
            is_favorite=is_favorite_val
        )

        if error:
            # Roll back stored file if DB insert failed.
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "Model photo uploaded.",
            "data": model_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"model photo upload error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload model photo: {str(e)}"
        )


@router.get("/api/model-photos")
async def get_model_photos(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Page size"),
        is_active: bool = Query(True, description="Only return active (non-soft-deleted) photos")
):
    """
    Paginated list of the current user's model photos.

    Args:
        token: auth token.
        db: DB session.
        page: page index (1-based).
        page_size: page size.
        is_active: when True, only rows with ``is_active`` True (soft-delete filter).

    Returns:
        ``photos`` and ``pagination`` under ``data``.
    """
    try:
        current_user = get_current_user(token, db)

        skip = (page - 1) * page_size

        photos, total, error = crud.model_photo_crud.get_model_photos_by_user(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            is_active=is_active
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "photos": photos,
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

    except HTTPException:
        raise
    except Exception as e:
        print(f"model photos list error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load model photos: {str(e)}"
        )


@router.get("/api/model-photos/primary")
async def get_primary_model_photo(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Return the user's primary (default) model photo for try-on.

    Args:
        token: auth token.
        db: DB session.

    Returns:
        Primary photo in ``data``, or ``data`` null with an informational message.
    """
    try:
        current_user = get_current_user(token, db)

        photo, error = crud.model_photo_crud.get_primary_model_photo(
            db=db,
            user_id=current_user.id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        if not photo:
            return {
                "success": True,
                "message": "No primary model photo is set yet.",
                "data": None
            }

        return {
            "success": True,
            "data": photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"primary model photo error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load primary model photo: {str(e)}"
        )


@router.put("/api/model-photos/{photo_id}")
async def update_model_photo(
        photo_id: int = Path(..., ge=1, description="Model photo id"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        photo_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        is_primary: Optional[bool] = Form(None),
        is_favorite: Optional[int] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    Update model photo metadata and optionally replace the image file.

    Args:
        photo_id: row id.
        token: auth token.
        db: DB session.
        photo_name: new name (optional).
        description: new description (optional).
        is_primary: set as primary (optional).
        is_favorite: set favorite level (0-3, optional).
        file: new image file (optional).

    Returns:
        Updated row in ``data``.
    """
    try:
        current_user = get_current_user(token, db)

        # Load row and enforce ownership
        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model photo not found or access denied."
            )

        image_url = photo.image_url
        if file:
            # New image: drop old file, save new file, refresh size/extension.
            delete_file(photo.image_url)
            image_url = save_upload_file(file, current_user.id)

            file_size = file.size
            file_ext = PathLib(file.filename).suffix.lower()
            file_format = file_ext[1:] if file_ext else None

            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary,
                "is_favorite": (max(0, min(3, int(is_favorite))) if is_favorite is not None else None),
                "image_url": image_url,
                "file_size": file_size,
                "file_format": file_format
            }
        else:
            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary,
                "is_favorite": (max(0, min(3, int(is_favorite))) if is_favorite is not None else None)
            }

        # Drop None so we only PATCH fields that were sent.
        update_data = {k: v for k, v in update_data.items() if v is not None}

        updated_photo, error = crud.model_photo_crud.update_model_photo(
            db=db,
            db_photo=photo,
            update_data=update_data
        )

        if error:
            # DB update failed after a new upload — remove the new file.
            if file:
                delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "Model photo updated.",
            "data": updated_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"model photo update error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update model photo: {str(e)}"
        )


@router.delete("/api/model-photos/{photo_id}")
async def delete_model_photo(
        photo_id: int = Path(..., ge=1, description="Model photo id"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        hard_delete: bool = Query(False, description="Permanently delete DB row and files from disk")
):
    """
    Soft-delete or hard-delete a model photo.

    Args:
        photo_id: row id.
        token: auth token.
        db: DB session.
        hard_delete: True removes the row and files; False sets ``is_active`` False (recoverable).

    Returns:
        Success message payload.
    """
    try:
        current_user = get_current_user(token, db)

        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model photo not found or access denied."
            )

        # Soft-delete (is_active=False) vs hard-delete (row removed).
        if hard_delete:
            success, error = crud.model_photo_crud.hard_delete_model_photo(
                db=db,
                photo_id=photo_id
            )
        else:
            success, error = crud.model_photo_crud.delete_model_photo(
                db=db,
                photo_id=photo_id
            )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # Physical files only for hard delete (soft delete keeps paths for possible restore).
        if hard_delete:
            delete_file(photo.image_url)
            if photo.thumbnail_url:
                delete_file(photo.thumbnail_url)

        return {
            "success": True,
            "message": f"Model photo {'permanently ' if hard_delete else ''}deleted."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"model photo delete error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete model photo: {str(e)}"
        )


@router.post("/api/model-photos/{photo_id}/set-primary")
async def set_primary_model_photo(
        photo_id: int = Path(..., ge=1, description="Model photo id"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    Mark this photo as the user's primary model photo.

    Other photos' ``is_primary`` flags are cleared in CRUD (single primary per user).

    Args:
        photo_id: row id to promote.
        token: auth token.
        db: DB session.

    Returns:
        Updated row in ``data``.
    """
    try:
        current_user = get_current_user(token, db)

        # Load row and enforce ownership
        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model photo not found or access denied."
            )

        # CRUD clears other primaries for this user when is_primary=True.
        updated_photo, error = crud.model_photo_crud.update_model_photo(
            db=db,
            db_photo=photo,
            update_data={"is_primary": True}
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "Set as primary model photo.",
            "data": updated_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"set primary model photo error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not set primary model photo: {str(e)}"
        )

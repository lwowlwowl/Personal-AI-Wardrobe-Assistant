"""模特照片 API（路徑與行為與重構前 main 一致）。"""
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


# ============ 模特照片管理API ============

@router.post("/api/model-photos/upload")
async def upload_model_photo(
        file: UploadFile = File(...),
        photo_name: str = Form(...),
        description: Optional[str] = Form(None),
        is_primary: Optional[str] = Form("false"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    上传模特照片（用于虚拟试衣功能）
    参数：
        file: 模特照片文件
        photo_name: 照片名称
        description: 照片描述（可选）
        is_primary: 是否设为主要照片（表单传 "true"/"false" 字符串，需解析为 bool）
        token: 用户认证令牌
        db: 数据库会话
    返回：
        上传成功的模特照片信息
    """
    try:
        # 表单中 is_primary 为字符串 "true"/"false"，Python 中 bool("false") 为 True，需显式解析
        is_primary_bool = str(is_primary).strip().lower() in ("true", "1", "on", "yes") if is_primary else False

        # 验证用户
        current_user = get_current_user(token, db)

        # 保存图片文件（复用文件上传函数）
        image_url = save_upload_file(file, current_user.id)

        # 获取文件信息
        file_size = file.size
        file_ext = PathLib(file.filename).suffix.lower()
        file_format = file_ext[1:] if file_ext else None

        # 创建模特照片记录
        model_photo, error = crud.model_photo_crud.create_model_photo(
            db=db,
            user_id=current_user.id,
            photo_name=photo_name,
            image_url=image_url,
            description=description,
            file_size=file_size,
            file_format=file_format,
            is_primary=is_primary_bool
        )

        if error:
            # 如果创建失败，删除已上传的图片
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
        print(f"上传模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload model photo: {str(e)}"
        )


@router.get("/api/model-photos")
async def get_model_photos(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        is_active: bool = Query(True, description="是否只显示激活的照片")
):
    """
    获取用户的模特照片列表
    参数：
        token: 用户认证令牌
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        is_active: 是否只显示激活的照片（软删除标记）
    返回：
        分页的模特照片列表
    """
    try:
        current_user = get_current_user(token, db)

        skip = (page - 1) * page_size

        # 调用CRUD函数获取模特照片
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

        # 计算总页数
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
        print(f"获取模特照片列表错误: {traceback.format_exc()}")
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
    获取用户的主要模特照片（用于虚拟试衣）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        用户的主要模特照片信息
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
        print(f"获取主要模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load primary model photo: {str(e)}"
        )


@router.put("/api/model-photos/{photo_id}")
async def update_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        photo_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        is_primary: Optional[bool] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    更新模特照片信息
    参数：
        photo_id: 要更新的模特照片ID
        token: 用户认证令牌
        db: 数据库会话
        photo_name: 新照片名称（可选）
        description: 新描述（可选）
        is_primary: 是否设为主要照片（可选）
        file: 新照片文件（可选）
    返回：
        更新后的模特照片信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片并验证所有权
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

        # 更新图片（如果有新图片）
        image_url = photo.image_url
        if file:
            # 删除旧图片
            delete_file(photo.image_url)
            # 保存新图片
            image_url = save_upload_file(file, current_user.id)

            # 更新文件信息
            file_size = file.size
            file_ext = PathLib(file.filename).suffix.lower()
            file_format = file_ext[1:] if file_ext else None

            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary,
                "image_url": image_url,
                "file_size": file_size,
                "file_format": file_format
            }
        else:
            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary
            }

        # 清理None值，只传递有值的字段
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # 更新模特照片信息
        updated_photo, error = crud.model_photo_crud.update_model_photo(
            db=db,
            db_photo=photo,
            update_data=update_data
        )

        if error:
            # 如果更新失败且上传了新图片，删除新图片
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
        print(f"更新模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update model photo: {str(e)}"
        )


@router.delete("/api/model-photos/{photo_id}")
async def delete_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        hard_delete: bool = Query(False, description="是否永久删除")
):
    """
    删除模特照片（支持软删除和硬删除）
    参数：
        photo_id: 要删除的模特照片ID
        token: 用户认证令牌
        db: 数据库会话
        hard_delete: 是否永久删除（True：硬删除，False：软删除）
    返回：
        删除结果
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片信息（用于可能的文件删除）
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

        # 根据参数选择删除方式
        if hard_delete:
            # 永久删除（从数据库完全移除）
            success, error = crud.model_photo_crud.hard_delete_model_photo(
                db=db,
                photo_id=photo_id
            )
        else:
            # 软删除（标记为删除，可恢复）
            success, error = crud.model_photo_crud.delete_model_photo(
                db=db,
                photo_id=photo_id
            )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 永久删除时才删除物理文件
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
        print(f"删除模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete model photo: {str(e)}"
        )


@router.post("/api/model-photos/{photo_id}/set-primary")
async def set_primary_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    设置模特照片为主要照片
    参数：
        photo_id: 要设为主要照片的ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的照片信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片并验证所有权
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

        # 更新为主要照片（会自动更新其他照片的is_primary状态）
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
        print(f"设置主要模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not set primary model photo: {str(e)}"
        )



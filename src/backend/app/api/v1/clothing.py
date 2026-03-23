"""衣物相關 API（路徑與行為與重構前 main 一致）。"""
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


# ============ 服装管理API ============
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
        tags: Optional[str] = Form(None),  # 以逗号分隔的标签字符串
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        auto_label: bool = Form(True),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    上传衣物图片并创建衣物记录
    参数：
        file: 衣物图片文件
        name: 衣物名称
        category: 衣物分类
        color: 颜色（可选）
        season: 适用季节（可选）
        brand: 品牌（可选）
        tags: 标签，逗号分隔（可选）
        description: 描述（可选）
        price: 价格（可选）
        purchase_date: 购买日期，YYYY-MM-DD格式（可选）
        token: 用户认证令牌
        db: 数据库会话
    返回：
        上传成功的衣物信息
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
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        category: Optional[str] = Query(None, description="分类筛选"),
        season: Optional[str] = Query(None, description="季节筛选"),
        color: Optional[str] = Query(None, description="颜色筛选"),
        brand: Optional[str] = Query(None, description="品牌筛选"),
        is_favorite: Optional[str] = Query(None, description="收藏等级筛选，支持逗号分隔多选如 0,1,2"),
        min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
        max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        order_by: str = Query("created_at", description="排序字段"),
        order_desc: bool = Query(True, description="是否降序")
):
    """
    获取用户的衣物列表（支持分页、筛选、搜索）
    参数：
        token: 用户认证令牌
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页数量，最大100
        category: 按分类筛选
        season: 按季节筛选
        color: 按颜色筛选
        brand: 按品牌筛选
        is_favorite: 按收藏状态筛选
        min_price: 最低价格筛选
        max_price: 最高价格筛选
        search: 搜索关键词（模糊匹配名称和描述）
        order_by: 排序字段
        order_desc: 是否降序排列
    返回：
        分页的衣物列表
    """
    try:
        current_user = get_current_user(token, db)

        # 解析 is_favorite：支持 "0,1,2" 或 "1" 格式
        is_favorite_parsed = None
        if is_favorite:
            try:
                levels = [int(x.strip()) for x in is_favorite.split(",") if x.strip()]
                levels = [x for x in levels if 0 <= x <= 3]
                if levels:
                    is_favorite_parsed = levels
            except ValueError:
                pass

        # 计算分页偏移量
        skip = (page - 1) * page_size

        # 调用CRUD函数获取衣物列表
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

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

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
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
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
    更新衣物信息
    参数：
        clothing_id: 要更新的衣物ID
        token: 用户认证令牌
        db: 数据库会话
        name: 新名称（可选）
        category: 新主分类（可选，后端 9 个枚举之一）
        subcategory: 新子分类（可选，用户自定义）
        color: 新颜色（可选）
        season: 新季节（可选）
        brand: 新品牌（可选）
        tags: 新标签（可选）
        description: 新描述（可选）
        price: 新价格（可选）
        purchase_date: 新购买日期（可选）
        is_favorite: 收藏状态（可选）
        condition: 衣物状况（可选）
        file: 新图片文件（可选）
    返回：
        更新后的衣物信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取衣物并验证所有权
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

        # 更新图片（如果有新图片）
        image_url = item.image_url
        if file:
            # 删除旧图片
            delete_file(item.image_url)
            # 保存新图片
            image_url = save_upload_file(file, current_user.id)

        # 解析标签字符串为列表
        tag_list = None
        if tags is not None:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        season_list = parse_season_form(season, allow_empty=True) if season is not None else None

        # 解析 is_favorite：0-3 整数
        is_favorite_val = None
        if is_favorite is not None and is_favorite.strip():
            try:
                v = int(is_favorite.strip())
                if 0 <= v <= 3:
                    is_favorite_val = v
            except ValueError:
                pass

        # 解析购买日期字符串为date对象
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = date.fromisoformat(purchase_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid purchase date. Use YYYY-MM-DD."
                )

        # 构建更新数据对象
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

        # 更新衣物信息
        updated_item, error = crud.clothing_crud.update_clothing_item(
            db=db,
            db_item=item,
            item_in=update_data
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
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    删除衣物
    参数：
        clothing_id: 要删除的衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        删除成功信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取衣物信息（用于后续删除图片文件）
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

        # 删除衣物记录（会级联删除相关标签等）
        success, error = crud.clothing_crud.delete_clothing_item(
            db=db,
            clothing_id=clothing_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 删除图片文件
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


# ============ 批量操作API ============

@router.post("/api/clothing/batch/delete")
async def batch_delete_clothing(
        clothing_ids: List[int],
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    批量删除衣物
    参数：
        clothing_ids: 要删除的衣物ID列表
        token: 用户认证令牌
        db: 数据库会话
    返回：
        批量删除结果
    """
    try:
        current_user = get_current_user(token, db)

        if not clothing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select at least one item to delete."
            )

        # 获取要删除的衣物信息（用于后续删除图片文件）
        items = db.query(models.ClothingItem).filter(
            models.ClothingItem.id.in_(clothing_ids),
            models.ClothingItem.user_id == current_user.id
        ).all()

        # 验证所有衣物都存在且属于当前用户
        if len(items) != len(clothing_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some items were not found or access was denied."
            )

        # 执行批量删除
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

        # 批量删除图片文件
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
    批量更新衣物信息
    参数：
        clothing_ids: 要更新的衣物ID列表
        update_data: 更新数据的字典
        token: 用户认证令牌
        db: 数据库会话
    返回：
        批量更新结果
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

        # 执行批量更新
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



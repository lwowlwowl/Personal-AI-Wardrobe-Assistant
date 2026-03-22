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
            detail=f"获取衣物列表时发生错误: {str(e)}"
        )


@router.get("/api/clothing/{clothing_id}")
async def get_clothing_detail(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取单件衣物的详细信息
    参数：
        clothing_id: 衣物ID，路径参数
        token: 用户认证令牌
        db: 数据库会话
    返回：
        衣物的完整详细信息
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权并获取衣物
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 刷新对象以加载关联的标签等延迟加载属性
        db.refresh(item)

        return {
            "success": True,
            "data": item
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing detail error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物详情时发生错误: {str(e)}"
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
                detail="衣物不存在或无权访问"
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
                    detail="购买日期格式错误，请使用YYYY-MM-DD格式"
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
            "message": "衣物更新成功",
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
            detail=f"更新衣物时发生错误: {str(e)}"
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
                detail="衣物不存在或无权访问"
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
            "message": "衣物删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing delete error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除衣物时发生错误: {str(e)}"
        )


@router.post("/api/clothing/{clothing_id}/toggle-favorite")
async def toggle_favorite(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    切换衣物的收藏状态
    参数：
        clothing_id: 衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的收藏状态
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 切换收藏等级：0->1->2->3->0 循环
        current = int(item.is_favorite) if item.is_favorite is not None else 0
        next_val = (current + 1) % 4
        update_data = schemas.ClothingItemUpdate(is_favorite=next_val)

        updated_item, error = crud.clothing_crud.update_clothing_item(
            db=db,
            db_item=item,
            item_in=update_data
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": f"已{'取消' if next_val == 0 else '设置'}收藏",
            "data": {
                "is_favorite": updated_item.is_favorite
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing toggle-favorite error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换收藏状态时发生错误: {str(e)}"
        )


@router.post("/api/clothing/{clothing_id}/record-wear")
async def record_clothing_wear(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    记录衣物穿着（增加穿着次数并更新最后穿着日期）
    参数：
        clothing_id: 衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的穿着统计信息
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 记录穿着（增加穿着次数，更新最后穿着日期为今天）
        updated_item, error = crud.clothing_crud.record_clothing_wear(
            db=db,
            clothing_id=clothing_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "穿着记录已更新",
            "data": {
                "wear_count": updated_item.wear_count,
                "last_worn_date": updated_item.last_worn_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing record-wear error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录穿着时发生错误: {str(e)}"
        )


# ============ 标签搜索API ============

@router.get("/api/clothing/tags/search")
async def search_by_tags(
        tag: str = Query(..., description="标签关键词"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    根据标签关键词搜索衣物（模糊匹配）
    参数：
        tag: 标签关键词
        token: 用户认证令牌
        db: 数据库会话
        page: 页码
        page_size: 每页数量
    返回：
        匹配标签的衣物列表
    """
    try:
        current_user = get_current_user(token, db)

        # 计算分页偏移量
        skip = (page - 1) * page_size

        # 直接查询标签表进行模糊匹配
        from sqlalchemy import or_

        # 构建查询：查找用户拥有的、标签包含关键词的衣物
        query = db.query(models.ClothingItem).join(
            models.ClothingTag,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingTag.tag.ilike(f"%{tag}%")  # 不区分大小写的模糊匹配
        ).distinct()  # 去重，避免同一衣物有多个匹配标签时重复出现

        total = query.count()

        # 分页查询
        items = query.offset(skip).limit(page_size).all()

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "items": items,
                "tag": tag,
                "total_count": total,
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
        print(f"clothing tags/search error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标签搜索时发生错误: {str(e)}"
        )


@router.get("/api/clothing/tags/popular")
async def get_popular_tags(
        token: str = Query(...),
        db: Session = Depends(get_db),
        limit: int = Query(20, ge=1, le=50, description="返回数量")
):
    """
    获取用户最常用的标签（按使用次数排序）
    参数：
        token: 用户认证令牌
        db: 数据库会话
        limit: 返回的标签数量上限
    返回：
        热门标签列表，包含标签名和使用次数
    """
    try:
        current_user = get_current_user(token, db)

        from sqlalchemy import func

        # 查询用户最常用的标签：按标签分组，统计每个标签的出现次数，按次数降序排列
        popular_tags = db.query(
            models.ClothingTag.tag,
            func.count(models.ClothingTag.id).label("count")
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).group_by(
            models.ClothingTag.tag
        ).order_by(
            func.count(models.ClothingTag.id).desc()  # 按标签使用次数降序
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {"tag": tag.tag, "count": tag.count}
                for tag in popular_tags
            ]
        }

    except Exception as e:
        print(f"clothing tags/popular error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门标签时发生错误: {str(e)}"
        )


@router.get("/api/clothing/tags/all")
async def get_all_tags(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户的所有标签（去重）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        用户使用的所有不重复标签列表
    """
    try:
        current_user = get_current_user(token, db)

        # 查询用户的所有标签（去重）
        all_tags = db.query(
            models.ClothingTag.tag
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).distinct().all()  # 使用distinct确保标签不重复

        return {
            "success": True,
            "data": [tag.tag for tag in all_tags]
        }

    except Exception as e:
        print(f"clothing tags/all error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取所有标签时发生错误: {str(e)}"
        )


# ============ 统计和分析API ============

@router.get("/api/clothing/stats")
async def get_clothing_stats(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户的衣物统计数据
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        衣物统计信息，如各类别数量、总价值等
    """
    try:
        current_user = get_current_user(token, db)

        # 调用CRUD函数获取统计信息
        stats = crud.clothing_crud.get_clothing_stats(
            db=db,
            user_id=current_user.id
        )

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        print(f"clothing stats error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据时发生错误: {str(e)}"
        )


@router.get("/api/clothing/filters")
async def get_filter_options(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物筛选选项（用于前端筛选器）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        所有可用的筛选选项，如颜色、品牌、季节等
    """
    try:
        current_user = get_current_user(token, db)

        # 调用CRUD函数获取筛选选项
        filters = crud.clothing_crud.get_filter_options(
            db=db,
            user_id=current_user.id
        )

        return {
            "success": True,
            "data": filters
        }

    except Exception as e:
        print(f"clothing filters error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取筛选选项时发生错误: {str(e)}"
        )

# ============ 分类和枚举API ============

@router.get("/api/clothing/categories")
async def get_clothing_categories():
    """
    获取衣物分类选项（从枚举中读取）
    返回：
        所有衣物分类、子分类、季节、状况等枚举选项
    """
    try:
        # 从模型定义的枚举中获取主分类
        categories = [
            {"value": category.value, "label": category.name}
            for category in models.ClothingCategory
        ]

        # 定义子分类映射（可以根据需要扩展）
        subcategories = {
            "top": [
                {"value": "t-shirt", "label": "T恤"},
                {"value": "shirt", "label": "衬衫"},
                {"value": "sweater", "label": "毛衣"},
                {"value": "hoodie", "label": "卫衣"},
                {"value": "blouse", "label": "女士衬衫"}
            ],
            "bottom": [
                {"value": "jeans", "label": "牛仔裤"},
                {"value": "pants", "label": "裤子"},
                {"value": "shorts", "label": "短裤"},
                {"value": "skirt", "label": "半身裙"}
            ],
            "dress": [
                {"value": "summer-dress", "label": "夏季连衣裙"},
                {"value": "evening-dress", "label": "晚礼服"},
                {"value": "casual-dress", "label": "休闲裙"}
            ],
            "outerwear": [
                {"value": "jacket", "label": "夹克"},
                {"value": "coat", "label": "大衣"},
                {"value": "windbreaker", "label": "风衣"}
            ],
            "footwear": [
                {"value": "sneakers", "label": "运动鞋"},
                {"value": "shoes", "label": "皮鞋"},
                {"value": "sandals", "label": "凉鞋"},
                {"value": "boots", "label": "靴子"}
            ]
        }

        # 返回所有枚举类型，用于前端表单
        return {
            "success": True,
            "data": {
                "categories": categories,
                "subcategories": subcategories,
                "seasons": [
                    {"value": season.value, "label": season.name}
                    for season in models.ClothingSeason
                ],
                "conditions": [
                    {"value": condition.value, "label": condition.name}
                    for condition in models.ClothingCondition
                ],
                "fit_types": [
                    {"value": fit_type.value, "label": fit_type.name}
                    for fit_type in models.ClothingFitType
                ],
                "patterns": [
                    {"value": pattern.value, "label": pattern.name}
                    for pattern in models.ClothingPattern
                ]
            }
        }

    except Exception as e:
        print(f"clothing categories error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类选项时发生错误: {str(e)}"
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
                detail="请选择要删除的衣物"
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
                detail="部分衣物不存在或无权访问"
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
            "message": f"成功删除 {deleted_count} 件衣物"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing batch/delete error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除时发生错误: {str(e)}"
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
                detail="请选择要更新的衣物"
            )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供更新数据"
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
            "message": f"成功更新 {updated_count} 件衣物"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"clothing batch/update error:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新时发生错误: {str(e)}"
        )



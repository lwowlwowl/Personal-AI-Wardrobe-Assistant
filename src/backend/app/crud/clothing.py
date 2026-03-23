"""衣物 CRUD。"""
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import ClothingItem, ClothingTag
from app.schemas import ClothingItemCreate, ClothingItemUpdate

class ClothingCRUD:
    """服装相关CRUD操作类"""

    @staticmethod
    def get_clothing_item_by_user(
            db: Session,
            user_id: int,
            clothing_id: int
    ) -> Optional[ClothingItem]:
        """
        获取用户的单个衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_id: 衣物ID

        返回:
            衣物对象，如果不存在或不属于用户则返回None
        """
        return db.query(ClothingItem).filter(
            ClothingItem.id == clothing_id,
            ClothingItem.user_id == user_id
        ).first()

    @staticmethod
    def get_clothing_items(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            season: Optional[str] = None,
            color: Optional[str] = None,
            brand: Optional[str] = None,
            is_favorite: Optional[List[int]] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            search: Optional[str] = None,
            order_by: str = "created_at",
            order_desc: bool = True
    ) -> Tuple[List[ClothingItem], int]:
        """
        获取衣物列表（支持过滤、搜索、排序、分页）

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数（用于分页）
            limit: 每页记录数
            category: 分类筛选
            season: 季节筛选
            color: 颜色筛选
            brand: 品牌筛选
            is_favorite: 收藏等级筛选，支持多选 [0,1,2,3]
            min_price: 最低价格
            max_price: 最高价格
            search: 搜索关键词
            order_by: 排序字段
            order_desc: 是否降序

        返回:
            Tuple[衣物列表, 总记录数]
        """
        # 基础查询：只查询当前用户的衣物，预加载 tags 供列表展示
        query = db.query(ClothingItem).options(joinedload(ClothingItem.tags)).filter(ClothingItem.user_id == user_id)

        # 应用过滤器
        if category:
            query = query.filter(ClothingItem.category == category)
        if season:
            query = query.filter(ClothingItem.season == season)
        if color:
            query = query.filter(ClothingItem.color == color)
        if brand:
            query = query.filter(ClothingItem.brand == brand)
        if is_favorite is not None:
            if isinstance(is_favorite, list):
                query = query.filter(ClothingItem.is_favorite.in_(is_favorite))
            else:
                query = query.filter(ClothingItem.is_favorite == is_favorite)
        if min_price is not None:
            query = query.filter(ClothingItem.price >= min_price)
        if max_price is not None:
            query = query.filter(ClothingItem.price <= max_price)

        # 搜索功能：支持名称、描述、品牌、风格的模糊搜索
        if search:
            search_filter = or_(
                ClothingItem.name.ilike(f"%{search}%"),
                ClothingItem.description.ilike(f"%{search}%"),
                ClothingItem.brand.ilike(f"%{search}%"),
                ClothingItem.style.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # 获取总数（用于分页计算）
        total = query.count()

        # 排序
        order_column = getattr(ClothingItem, order_by, ClothingItem.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 分页
        items = query.offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def create_clothing_item(
            db: Session,
            user_id: int,
            item_in: ClothingItemCreate,
            image_url: str,
            thumbnail_url: Optional[str] = None
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        创建衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            item_in: 衣物创建数据
            image_url: 图片URL
            thumbnail_url: 缩略图URL（可选）

        返回:
            Tuple[创建的衣物对象, 错误信息]
        """
        try:
            # 创建衣物对象，排除tags字段（后续单独处理）
            db_item = ClothingItem(
                user_id=user_id,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                **item_in.model_dump(exclude={"tags"})
            )
            db.add(db_item)
            db.flush()

            # 添加标签
            if item_in.tags:
                # 去重（同一衣物不可重复标签）；同时去掉空白
                seen = set()
                deduped_tags = []
                for raw in item_in.tags:
                    t = (raw or "").strip()
                    if not t:
                        continue
                    key = t.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped_tags.append(t)

                for tag_name in deduped_tags:
                    db.add(ClothingTag(clothing_id=db_item.id, tag=tag_name))

            try:
                db.commit()
            except IntegrityError:
                # 极少数情况下可能出现并发/重复写入，回滚后重试一次：跳过已存在的标签
                db.rollback()
                db.add(db_item)
                db.flush()
                for tag_name in (deduped_tags if item_in.tags else []):
                    exists = db.query(ClothingTag.id).filter(
                        ClothingTag.clothing_id == db_item.id,
                        ClothingTag.tag == tag_name
                    ).first()
                    if exists:
                        continue
                    db.add(ClothingTag(clothing_id=db_item.id, tag=tag_name))
                db.commit()

            db.refresh(db_item)

            return db_item, None

        except Exception as e:
            db.rollback()
            print(f"创建衣物错误: {e}")
            return None, f"Failed to create clothing item: {str(e)}"

    @staticmethod
    def update_clothing_item(
            db: Session,
            db_item: ClothingItem,
            item_in: ClothingItemUpdate
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        更新衣物

        参数:
            db: 数据库会话
            db_item: 要更新的衣物对象
            item_in: 更新数据

        返回:
            Tuple[更新后的衣物对象, 错误信息]
        """
        try:
            # 获取更新数据，排除未设置的字段和tags字段
            update_data = item_in.model_dump(exclude_unset=True, exclude={"tags"})

            # 更新衣物属性
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_item, field, value)

            # 更新标签（如果提供了）
            if item_in.tags is not None:
                # 删除现有标签
                db.query(ClothingTag).filter(
                    ClothingTag.clothing_id == db_item.id
                ).delete(synchronize_session=False)

                # 添加新标签
                if item_in.tags:
                    seen = set()
                    for raw in item_in.tags:
                        t = (raw or "").strip()
                        if not t:
                            continue
                        key = t.lower()
                        if key in seen:
                            continue
                        seen.add(key)
                        db.add(ClothingTag(clothing_id=db_item.id, tag=t))

            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            return db_item, None

        except Exception as e:
            db.rollback()
            print(f"更新衣物错误: {e}")
            return None, f"Failed to update clothing item: {str(e)}"

    @staticmethod
    def delete_clothing_item(db: Session, clothing_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除衣物

        参数:
            db: 数据库会话
            clothing_id: 衣物ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            item = db.query(ClothingItem).filter(ClothingItem.id == clothing_id).first()
            if not item:
                return False, "Clothing item does not exist"

            db.delete(item)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除衣物错误: {e}")
            return False, f"Failed to delete clothing item: {str(e)}"


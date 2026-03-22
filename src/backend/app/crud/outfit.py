"""搭配 CRUD。"""
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.models import ClothingItem, Outfit, OutfitItem
from app.schemas import OutfitCreate, OutfitUpdate

class OutfitCRUD:
    """搭配CRUD操作类"""

    @staticmethod
    def get_outfit(db: Session, outfit_id: int) -> Optional[Outfit]:
        """获取单个搭配（包含关联的衣物）"""
        return db.query(Outfit).options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).filter(Outfit.id == outfit_id).first()

    @staticmethod
    def get_outfit_by_user(
            db: Session,
            user_id: int,
            outfit_id: int
    ) -> Optional[Outfit]:
        """
        获取用户的单个搭配

        参数:
            db: 数据库会话
            user_id: 用户ID
            outfit_id: 搭配ID

        返回:
            搭配对象，包含关联的衣物信息
        """
        return db.query(Outfit).options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).filter(
            Outfit.id == outfit_id,
            Outfit.user_id == user_id
        ).first()

    @staticmethod
    def get_outfits(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            occasion: Optional[str] = None,
            season: Optional[str] = None,
            is_public: Optional[bool] = None,
            order_by: str = "created_at",
            order_desc: bool = True
    ) -> Tuple[List[Outfit], int]:
        """
        获取搭配列表（支持过滤、排序、分页）

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 每页记录数
            occasion: 场合筛选
            season: 季节筛选
            is_public: 是否公开
            order_by: 排序字段
            order_desc: 是否降序

        返回:
            Tuple[搭配列表, 总记录数]
        """
        query = db.query(Outfit).filter(Outfit.user_id == user_id)

        # 应用过滤器
        if occasion:
            query = query.filter(Outfit.occasion == occasion)
        if season:
            query = query.filter(Outfit.season == season)
        if is_public is not None:
            query = query.filter(Outfit.is_public == is_public)

        # 获取总数
        total = query.count()

        # 排序
        order_column = getattr(Outfit, order_by, Outfit.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # 分页并加载关联（预加载搭配项和衣物信息）
        items = query.options(
            joinedload(Outfit.outfit_items).joinedload(OutfitItem.clothing_item)
        ).offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def create_outfit(
            db: Session,
            user_id: int,
            outfit_in: OutfitCreate
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        创建搭配

        参数:
            db: 数据库会话
            user_id: 用户ID
            outfit_in: 搭配创建数据

        返回:
            Tuple[创建的搭配对象, 错误信息]
        """
        try:
            # 创建搭配
            db_outfit = Outfit(
                user_id=user_id,
                **outfit_in.model_dump(exclude={"clothing_items"})
            )
            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            # 添加搭配物品
            for item_in in outfit_in.clothing_items:
                # 验证衣物属于该用户
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == item_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()

                if not clothing:
                    db.rollback()
                    return None, f"衣物 {item_in.clothing_id} 不存在或不属于当前用户"

                # 创建搭配项
                outfit_item = OutfitItem(
                    outfit_id=db_outfit.id,
                    clothing_id=item_in.clothing_id,
                    position=item_in.position,
                    order_index=item_in.order_index
                )
                db.add(outfit_item)

            db.commit()
            db.refresh(db_outfit)

            return db_outfit, None

        except Exception as e:
            db.rollback()
            print(f"创建搭配错误: {e}")
            return None, f"创建搭配失败: {str(e)}"

    @staticmethod
    def update_outfit(
            db: Session,
            db_outfit: Outfit,
            outfit_in: OutfitUpdate
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        更新搭配

        参数:
            db: 数据库会话
            db_outfit: 要更新的搭配对象
            outfit_in: 更新数据

        返回:
            Tuple[更新后的搭配对象, 错误信息]
        """
        try:
            # 获取更新数据，排除未设置的字段
            update_data = outfit_in.model_dump(exclude_unset=True)

            # 更新搭配属性
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_outfit, field, value)

            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            return db_outfit, None

        except Exception as e:
            db.rollback()
            print(f"更新搭配错误: {e}")
            return None, f"更新搭配失败: {str(e)}"

    @staticmethod
    def delete_outfit(db: Session, outfit_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除搭配

        参数:
            db: 数据库会话
            outfit_id: 搭配ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return False, "搭配不存在"

            db.delete(outfit)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除搭配错误: {e}")
            return False, f"删除搭配失败: {str(e)}"

    @staticmethod
    def record_outfit_wear(
            db: Session,
            outfit_id: int
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        记录搭配穿着（增加穿着次数并更新最后穿着日期）

        参数:
            db: 数据库会话
            outfit_id: 搭配ID

        返回:
            Tuple[更新后的搭配对象, 错误信息]
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return None, "搭配不存在"

            # 更新穿着统计
            outfit.wear_count += 1
            outfit.last_worn_date = date.today()
            db.add(outfit)
            db.commit()
            db.refresh(outfit)

            return outfit, None

        except Exception as e:
            db.rollback()
            print(f"记录搭配穿着错误: {e}")
            return None, f"记录搭配穿着失败: {str(e)}"

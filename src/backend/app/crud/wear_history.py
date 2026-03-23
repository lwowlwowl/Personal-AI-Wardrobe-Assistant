"""穿着记录 CRUD。"""
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import ClothingItem, Outfit, WearHistory
from app.schemas import WearHistoryCreate

class WearHistoryCRUD:
    """穿着记录CRUD操作类"""

    @staticmethod
    def create_wear_history(
            db: Session,
            user_id: int,
            history_in: WearHistoryCreate
    ) -> Tuple[Optional[WearHistory], Optional[str]]:
        """
        创建穿着记录

        参数:
            db: 数据库会话
            user_id: 用户ID
            history_in: 穿着记录数据

        返回:
            Tuple[创建的穿着记录对象, 错误信息]
        """
        try:
            # 创建穿着记录
            db_history = WearHistory(
                user_id=user_id,
                **history_in.model_dump()
            )
            db.add(db_history)

            # 更新衣物的穿着记录
            if history_in.clothing_id:
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == history_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()
                if clothing:
                    clothing.wear_count += 1
                    clothing.last_worn_date = history_in.wear_date

            # 更新搭配的穿着记录
            if history_in.outfit_id:
                outfit = db.query(Outfit).filter(
                    Outfit.id == history_in.outfit_id,
                    Outfit.user_id == user_id
                ).first()
                if outfit:
                    outfit.wear_count += 1
                    outfit.last_worn_date = history_in.wear_date

            db.commit()
            db.refresh(db_history)

            return db_history, None

        except Exception as e:
            db.rollback()
            print(f"创建穿着记录错误: {e}")
            return None, f"Could not save wear record: {str(e)}"

    @staticmethod
    def get_wear_history(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[WearHistory], int]:
        """
        获取穿着记录列表

        参数:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过的记录数
            limit: 每页记录数

        返回:
            Tuple[穿着记录列表, 总记录数]
        """
        query = db.query(WearHistory).filter(WearHistory.user_id == user_id)

        total = query.count()
        items = query.order_by(desc(WearHistory.wear_date)).offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def delete_wear_history(db: Session, history_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除穿着记录

        参数:
            db: 数据库会话
            history_id: 穿着记录ID

        返回:
            Tuple[是否成功, 错误信息]
        """
        try:
            history = db.query(WearHistory).filter(WearHistory.id == history_id).first()
            if not history:
                return False, "Record does not exist"

            clothing_id = history.clothing_id
            user_id = history.user_id
            db.delete(history)
            db.flush()
            if clothing_id is not None:
                WearHistoryCRUD.recompute_clothing_after_removal(db, user_id, [clothing_id])
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"删除穿着记录错误: {e}")
            return False, f"Failed to delete wear record: {str(e)}"

    @staticmethod
    def recompute_clothing_after_removal(
            db: Session,
            user_id: int,
            clothing_ids: List[int],
    ) -> None:
        """
        删除部分穿着记录后，重算这些衣物的 wear_count 与 last_worn_date。
        假定调用前已对 wear_history 做了删除并 flush，本方法根据剩余记录更新衣物表。
        """
        for cid in clothing_ids:
            if cid is None:
                continue
            clothing = db.query(ClothingItem).filter(
                ClothingItem.id == cid,
                ClothingItem.user_id == user_id,
            ).first()
            if not clothing:
                continue
            clothing.wear_count = max(0, (clothing.wear_count or 0) - 1)
            latest = (
                db.query(WearHistory)
                .filter(
                    WearHistory.user_id == user_id,
                    WearHistory.clothing_id == cid,
                )
                .order_by(desc(WearHistory.wear_date))
                .limit(1)
                .first()
            )
            clothing.last_worn_date = latest.wear_date if latest else None

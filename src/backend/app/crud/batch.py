"""批量操作 CRUD。"""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import ClothingItem

class BatchCRUD:
    """批量操作CRUD类"""

    @staticmethod
    def batch_update_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int],
            update_data: Dict[str, Any]
    ) -> Tuple[int, Optional[str]]:
        """
        批量更新衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_ids: 衣物ID列表
            update_data: 更新数据字典

        返回:
            Tuple[更新的记录数, 错误信息]
        """
        try:
            # 验证所有衣物都属于该用户
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "Some items do not exist or do not belong to the current user"

            # 批量更新（使用synchronize_session=False提高性能）
            updated_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).update(update_data, synchronize_session=False)

            db.commit()
            return updated_count, None

        except Exception as e:
            db.rollback()
            print(f"批量更新错误: {e}")
            return 0, f"Bulk update failed: {str(e)}"

    @staticmethod
    def batch_delete_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int]
    ) -> Tuple[int, Optional[str]]:
        """
        批量删除衣物

        参数:
            db: 数据库会话
            user_id: 用户ID
            clothing_ids: 衣物ID列表

        返回:
            Tuple[删除的记录数, 错误信息]
        """
        try:
            # 验证所有衣物都属于该用户
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "Some items do not exist or do not belong to the current user"

            # 批量删除（使用synchronize_session=False提高性能）
            deleted_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).delete(synchronize_session=False)

            db.commit()
            return deleted_count, None

        except Exception as e:
            db.rollback()
            print(f"批量删除错误: {e}")
            return 0, f"Bulk delete failed: {str(e)}"

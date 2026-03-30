"""Bulk clothing operations CRUD."""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import ClothingItem

class BatchCRUD:
    """Bulk update/delete for clothing."""

    @staticmethod
    def batch_update_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int],
            update_data: Dict[str, Any]
    ) -> Tuple[int, Optional[str]]:
        """
        Bulk-update clothing rows.

        Args:
            db: DB session
            user_id: owner id
            clothing_ids: ids to update
            update_data: column dict

        Returns:
            (rows_updated, error_message)
        """
        try:
            # Every id must exist and belong to this user.
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "Some items do not exist or do not belong to the current user"

            # Bulk UPDATE; synchronize_session=False is faster for large sets.
            updated_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).update(update_data, synchronize_session=False)

            db.commit()
            return updated_count, None

        except Exception as e:
            db.rollback()
            print(f"batch_update_clothing error: {e}")
            return 0, f"Bulk update failed: {str(e)}"

    @staticmethod
    def batch_delete_clothing(
            db: Session,
            user_id: int,
            clothing_ids: List[int]
    ) -> Tuple[int, Optional[str]]:
        """
        Bulk-delete clothing rows.

        Args:
            db: DB session
            user_id: owner id
            clothing_ids: ids to delete

        Returns:
            (rows_deleted, error_message)
        """
        try:
            # Every id must exist and belong to this user.
            items = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids),
                ClothingItem.user_id == user_id
            ).all()

            if len(items) != len(clothing_ids):
                return 0, "Some items do not exist or do not belong to the current user"

            # Bulk DELETE; synchronize_session=False avoids loading full rows.
            deleted_count = db.query(ClothingItem).filter(
                ClothingItem.id.in_(clothing_ids)
            ).delete(synchronize_session=False)

            db.commit()
            return deleted_count, None

        except Exception as e:
            db.rollback()
            print(f"batch_delete_clothing error: {e}")
            return 0, f"Bulk delete failed: {str(e)}"

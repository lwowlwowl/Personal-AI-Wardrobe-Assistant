"""Wear history CRUD."""
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import ClothingItem, Outfit, WearHistory
from app.schemas import WearHistoryCreate

class WearHistoryCRUD:
    """CRUD helpers for wear history."""

    @staticmethod
    def create_wear_history(
            db: Session,
            user_id: int,
            history_in: WearHistoryCreate
    ) -> Tuple[Optional[WearHistory], Optional[str]]:
        """
        Create a wear-history row.

        Args:
            db: DB session
            user_id: owner id
            history_in: payload

        Returns:
            (row, error_message)
        """
        try:
            db_history = WearHistory(
                user_id=user_id,
                **history_in.model_dump()
            )
            db.add(db_history)

            # Denormalized counters on the linked clothing row, if any.
            if history_in.clothing_id:
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == history_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()
                if clothing:
                    clothing.wear_count += 1
                    clothing.last_worn_date = history_in.wear_date

            # Same for outfit wear stats.
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
            print(f"create_wear_history error: {e}")
            return None, f"Could not save wear record: {str(e)}"

    @staticmethod
    def get_wear_history(
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> Tuple[List[WearHistory], int]:
        """
        List wear history for a user.

        Args:
            db: DB session
            user_id: owner id
            skip, limit: pagination

        Returns:
            (rows, total)
        """
        query = db.query(WearHistory).filter(WearHistory.user_id == user_id)

        total = query.count()
        # Sort by wear_date descending (most recent first).
        items = query.order_by(desc(WearHistory.wear_date)).offset(skip).limit(limit).all()

        return items, total

    @staticmethod
    def delete_wear_history(db: Session, history_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete one wear-history row.

        Args:
            db: DB session
            history_id: row id

        Returns:
            (success, error_message)
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
            print(f"delete_wear_history error: {e}")
            return False, f"Failed to delete wear record: {str(e)}"

    @staticmethod
    def recompute_clothing_after_removal(
            db: Session,
            user_id: int,
            clothing_ids: List[int],
    ) -> None:
        """
        After removing wear_history rows, recompute wear_count and last_worn_date for affected items.
        Caller should have deleted/flushed history rows before calling.
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

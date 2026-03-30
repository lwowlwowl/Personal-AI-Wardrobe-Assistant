"""Outfit CRUD."""
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.models import ClothingItem, Outfit, OutfitItem
from app.schemas import OutfitCreate, OutfitUpdate

class OutfitCRUD:
    """CRUD helpers for outfits."""

    @staticmethod
    def get_outfit(db: Session, outfit_id: int) -> Optional[Outfit]:
        """Load one outfit with related clothing rows."""
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
        Load one outfit for a user (with items).

        Args:
            db: DB session
            user_id: owner id
            outfit_id: outfit id

        Returns:
            Outfit or None.
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
        List outfits with filters and pagination.

        Args:
            db: DB session
            user_id: owner id
            skip, limit: pagination
            occasion, season, is_public: filters
            order_by, order_desc: sort

        Returns:
            (outfits, total)
        """
        query = db.query(Outfit).filter(Outfit.user_id == user_id)

        # Filters
        if occasion:
            query = query.filter(Outfit.occasion == occasion)
        if season:
            query = query.filter(Outfit.season == season)
        if is_public is not None:
            query = query.filter(Outfit.is_public == is_public)

        total = query.count()

        # Sort
        order_column = getattr(Outfit, order_by, Outfit.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Page + eager-load outfit lines and clothing rows
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
        Create an outfit and its items.

        Args:
            db: DB session
            user_id: owner id
            outfit_in: create payload

        Returns:
            (outfit, error_message)
        """
        try:
            db_outfit = Outfit(
                user_id=user_id,
                **outfit_in.model_dump(exclude={"clothing_items"})
            )
            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            # One OutfitItem per slot; each clothing_id must belong to this user.
            for item_in in outfit_in.clothing_items:
                clothing = db.query(ClothingItem).filter(
                    ClothingItem.id == item_in.clothing_id,
                    ClothingItem.user_id == user_id
                ).first()

                if not clothing:
                    db.rollback()
                    return None, f"Clothing item {item_in.clothing_id} does not exist or does not belong to the current user"

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
            print(f"create_outfit error: {e}")
            return None, f"Failed to create outfit: {str(e)}"

    @staticmethod
    def update_outfit(
            db: Session,
            db_outfit: Outfit,
            outfit_in: OutfitUpdate
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        Update outfit scalar fields.

        Args:
            db: DB session
            db_outfit: existing row
            outfit_in: update payload

        Returns:
            (outfit, error_message)
        """
        try:
            update_data = outfit_in.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                if value is not None:
                    setattr(db_outfit, field, value)

            db.add(db_outfit)
            db.commit()
            db.refresh(db_outfit)

            return db_outfit, None

        except Exception as e:
            db.rollback()
            print(f"update_outfit error: {e}")
            return None, f"Failed to update outfit: {str(e)}"

    @staticmethod
    def delete_outfit(db: Session, outfit_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete an outfit.

        Args:
            db: DB session
            outfit_id: outfit id

        Returns:
            (success, error_message)
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return False, "Outfit does not exist"

            db.delete(outfit)
            db.commit()
            return True, None

        except Exception as e:
            db.rollback()
            print(f"delete_outfit error: {e}")
            return False, f"Failed to delete outfit: {str(e)}"

    @staticmethod
    def record_outfit_wear(
            db: Session,
            outfit_id: int
    ) -> Tuple[Optional[Outfit], Optional[str]]:
        """
        Increment wear_count and set last_worn_date to today.

        Args:
            db: DB session
            outfit_id: outfit id

        Returns:
            (outfit, error_message)
        """
        try:
            outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()
            if not outfit:
                return None, "Outfit does not exist"

            outfit.wear_count += 1
            outfit.last_worn_date = date.today()
            db.add(outfit)
            db.commit()
            db.refresh(outfit)

            return outfit, None

        except Exception as e:
            db.rollback()
            print(f"record_outfit_wear error: {e}")
            return None, f"Failed to record outfit wear: {str(e)}"

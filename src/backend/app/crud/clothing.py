"""Clothing CRUD."""
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import ClothingItem, ClothingTag
from app.schemas import ClothingItemCreate, ClothingItemUpdate

class ClothingCRUD:
    """CRUD helpers for clothing items."""

    @staticmethod
    def get_clothing_item_by_user(
            db: Session,
            user_id: int,
            clothing_id: int
    ) -> Optional[ClothingItem]:
        """
        Get one clothing item for a user.

        Args:
            db: DB session
            user_id: owner id
            clothing_id: item id

        Returns:
            ClothingItem or None if missing or not owned.
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
        List clothing with filters, search, sort, and pagination.

        Args:
            db: DB session
            user_id: owner id
            skip: offset
            limit: page size
            category, season, color, brand: filters
            is_favorite: favorite levels, multi [0,1,2,3]
            min_price, max_price: price range
            search: fuzzy on name, description, brand, style
            order_by: column name
            order_desc: descending when True

        Returns:
            (items, total_count)
        """
        # Base query: this user's items only; eager-load tags for list UIs.
        query = db.query(ClothingItem).options(joinedload(ClothingItem.tags)).filter(ClothingItem.user_id == user_id)

        # Filters
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

        # Fuzzy search on name, description, brand, style
        if search:
            search_filter = or_(
                ClothingItem.name.ilike(f"%{search}%"),
                ClothingItem.description.ilike(f"%{search}%"),
                ClothingItem.brand.ilike(f"%{search}%"),
                ClothingItem.style.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        total = query.count()

        # Sort
        order_column = getattr(ClothingItem, order_by, ClothingItem.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Pagination
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
        Create a clothing item.

        Args:
            db: DB session
            user_id: owner id
            item_in: create payload
            image_url, thumbnail_url: media URLs

        Returns:
            (item, error_message)
        """
        try:
            # Create row without tags (tags handled below).
            db_item = ClothingItem(
                user_id=user_id,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                **item_in.model_dump(exclude={"tags"})
            )
            db.add(db_item)
            db.flush()

            # Dedupe tag strings; skip blanks; same tag not twice per item.
            deduped_tags = []
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
                    deduped_tags.append(t)

                for tag_name in deduped_tags:
                    db.add(ClothingTag(clothing_id=db_item.id, tag=tag_name))

            try:
                db.commit()
            except IntegrityError:
                # Rare race: duplicate tag row; retry insert skipping existing tags.
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
            print(f"create_clothing_item error: {e}")
            return None, f"Failed to create clothing item: {str(e)}"

    @staticmethod
    def update_clothing_item(
            db: Session,
            db_item: ClothingItem,
            item_in: ClothingItemUpdate
    ) -> Tuple[Optional[ClothingItem], Optional[str]]:
        """
        Update a clothing item.

        Args:
            db: DB session
            db_item: existing row
            item_in: update payload

        Returns:
            (item, error_message)
        """
        try:
            # Only fields explicitly set; tags handled separately.
            update_data = item_in.model_dump(exclude_unset=True, exclude={"tags"})

            for field, value in update_data.items():
                if value is not None:
                    setattr(db_item, field, value)

            # Replace tags when provided (None = leave unchanged at API level).
            if item_in.tags is not None:
                db.query(ClothingTag).filter(
                    ClothingTag.clothing_id == db_item.id
                ).delete(synchronize_session=False)

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
            print(f"update_clothing_item error: {e}")
            return None, f"Failed to update clothing item: {str(e)}"

    @staticmethod
    def delete_clothing_item(db: Session, clothing_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a clothing item.

        Args:
            db: DB session
            clothing_id: item id

        Returns:
            (success, error_message)
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
            print(f"delete_clothing_item error: {e}")
            return False, f"Failed to delete clothing item: {str(e)}"

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Outfit(Base):
    """
    Saved outfit (composed of multiple clothing items).
    """
    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    occasion = Column(String(100), nullable=True)
    season = Column(String(20), nullable=True)
    style = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=False)
    wear_count = Column(Integer, default=0)
    last_worn_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="outfits")
    outfit_items = relationship("OutfitItem", back_populates="outfit", cascade="all, delete-orphan")
    wear_history = relationship("WearHistory", back_populates="outfit")

    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_outfit_rating'),
        Index('idx_outfits_user_created', 'user_id', 'created_at'),
        Index('idx_outfits_occasion', 'occasion'),
        Index('idx_outfits_season', 'season'),
    )


class OutfitItem(Base):
    """
    Join table: outfit ↔ clothing with slot and order.
    """
    __tablename__ = "outfit_items"

    id = Column(Integer, primary_key=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False)
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)
    position = Column(String(20), nullable=False)
    order_index = Column(Integer, default=0)

    outfit = relationship("Outfit", back_populates="outfit_items")
    clothing_item = relationship("ClothingItem", back_populates="outfit_items")

    __table_args__ = (
        UniqueConstraint('outfit_id', 'clothing_id', name='uq_outfit_clothing'),
        Index('idx_outfit_items_outfit', 'outfit_id', 'order_index'),
        Index('idx_outfit_items_clothing', 'clothing_id'),
    )

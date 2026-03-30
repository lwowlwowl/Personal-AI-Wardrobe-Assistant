from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WearHistory(Base):
    """
    Wear history: records when the user wore a clothing item and/or an outfit.
    """
    __tablename__ = "wear_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # owner user
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="SET NULL"), nullable=True)  # optional; null when logging outfit-only
    outfit_id = Column(Integer, ForeignKey("outfits.id", ondelete="SET NULL"), nullable=True)  # optional; null when logging single-item only

    wear_date = Column(Date, nullable=False)  # calendar date worn
    weather = Column(String(100), nullable=True)  # free-text weather
    temperature = Column(Integer, nullable=True)  # degrees Celsius
    location = Column(String(200), nullable=True)  # place
    occasion = Column(String(100), nullable=True)  # occasion
    notes = Column(Text, nullable=True)  # notes
    rating = Column(Integer, nullable=True)  # wear rating 1–5 (see CheckConstraint)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # row creation time

    # Relationships
    user = relationship("User", back_populates="wear_history")  # owning user
    clothing_item = relationship("ClothingItem", back_populates="wear_history")  # linked item (optional)
    outfit = relationship("Outfit", back_populates="wear_history")  # linked outfit (optional)

    # Table-level constraints and indexes
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_wear_history_rating'),  # rating range
        Index('idx_wear_history_user_date', 'user_id', 'wear_date'),  # by user and wear date
        Index('idx_wear_history_clothing', 'clothing_id'),  # by clothing item
        Index('idx_wear_history_outfit', 'outfit_id'),  # by outfit
        Index('idx_wear_history_date', 'wear_date'),  # by date
    )

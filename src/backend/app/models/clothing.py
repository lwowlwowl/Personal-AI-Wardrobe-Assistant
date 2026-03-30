import enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ClothingCategory(str, enum.Enum):
    """Primary clothing category (API / DB enum)."""
    TOP = "top"  # tops
    BOTTOM = "bottom"  # bottoms
    DRESS = "dress"  # dresses
    OUTERWEAR = "outerwear"  # outerwear
    FOOTWEAR = "footwear"  # shoes
    ACCESSORY = "accessory"  # accessories
    BAG = "bag"  # bags
    UNDERWEAR = "underwear"  # underwear
    OTHER = "other"  # other


class ClothingSeason(str, enum.Enum):
    """Season tag."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"  # year-round


class ClothingCondition(str, enum.Enum):
    """Wear / quality condition."""
    NEW = "new"  # like new
    GOOD = "good"  # good
    FAIR = "fair"  # fair
    POOR = "poor"  # poor


class ClothingFitType(str, enum.Enum):
    """Fit / silhouette."""
    SLIM = "slim"  # slim
    REGULAR = "regular"  # regular
    LOOSE = "loose"  # relaxed
    OVERSIZED = "oversized"  # oversized


class ClothingPattern(str, enum.Enum):
    """Pattern / print."""
    SOLID = "solid"  # solid
    STRIPED = "striped"  # stripes
    CHECKED = "checked"  # checks
    PRINTED = "printed"  # print
    PLAID = "plaid"  # plaid
    DOTTED = "dotted"  # dots
    OTHER = "other"  # other


class ClothingItem(Base):
    """
    One wardrobe item belonging to a user (image + attributes + tags).
    """
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # owner

    # Basic info
    name = Column(String(200), nullable=False)  # display name
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)

    # Taxonomy
    category = Column(SQLEnum(ClothingCategory), nullable=False)  # primary category
    subcategory = Column(String(100), nullable=True)  # free text, e.g. T-shirt
    style = Column(String(100), nullable=True)  # e.g. casual, business

    # Appearance
    color = Column(String(50), nullable=True)
    color_code = Column(String(7), nullable=True)  # #RRGGBB
    pattern = Column(SQLEnum(ClothingPattern), nullable=True)
    brand = Column(String(100), nullable=True)

    # Physical
    material = Column(String(100), nullable=True)
    size = Column(String(20), nullable=True)
    fit_type = Column(SQLEnum(ClothingFitType), nullable=True)

    # Usage
    season = Column(ARRAY(SQLEnum(ClothingSeason)), nullable=True)  # one or more seasons
    occasion = Column(String(100), nullable=True)
    purchase_date = Column(Date, nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    purchase_location = Column(String(200), nullable=True)

    # Status
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Integer, default=0)  # 0–3 (UI “hearts”)
    wear_count = Column(Integer, default=0)
    last_worn_date = Column(Date, nullable=True)
    condition = Column(SQLEnum(ClothingCondition), default=ClothingCondition.NEW)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    custom_metadata = Column(JSON, nullable=True)  # app-specific JSON

    user = relationship("User", back_populates="clothing_items")
    tags = relationship("ClothingTag", back_populates="clothing_item", cascade="all, delete-orphan")
    outfit_items = relationship("OutfitItem", back_populates="clothing_item", cascade="all, delete-orphan")
    wear_history = relationship("WearHistory", back_populates="clothing_item")

    __table_args__ = (
        Index('idx_clothing_user_created', 'user_id', 'created_at'),
        Index('idx_clothing_category', 'category'),
        Index('idx_clothing_season', 'season', postgresql_using="gin"),
        Index('idx_clothing_brand', 'brand'),
        Index('idx_clothing_color', 'color'),
    )


class ClothingTag(Base):
    """
    Tag string attached to a clothing item (unique per item+tag).
    """
    __tablename__ = "clothing_tags"

    id = Column(Integer, primary_key=True, index=True)
    clothing_id = Column(Integer, ForeignKey("clothing_items.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(50), nullable=False)
    tag_type = Column(String(20), default="custom")  # e.g. custom, system
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    clothing_item = relationship("ClothingItem", back_populates="tags")

    __table_args__ = (
        UniqueConstraint('clothing_id', 'tag', name='uq_clothing_tag'),
        Index('idx_clothing_tags_clothing_id', 'clothing_id'),
        Index('idx_clothing_tags_tag', 'tag'),
    )

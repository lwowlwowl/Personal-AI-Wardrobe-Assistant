from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clothing import ClothingSeason


class OutfitItemBase(BaseModel):
    """One clothing slot inside an outfit."""
    clothing_id: int = Field(..., description="Clothing item id")
    position: str = Field(..., max_length=20, description="Slot e.g. top, bottom")
    order_index: int = Field(0, description="Display order")


class OutfitItemCreate(OutfitItemBase):
    """Create outfit item."""
    pass


class OutfitItem(OutfitItemBase):
    """Outfit item with ids."""
    id: int
    outfit_id: int

    model_config = ConfigDict(from_attributes=True)


class OutfitBase(BaseModel):
    """Shared outfit fields."""
    name: str = Field(..., max_length=200, description="Outfit name")
    description: Optional[str] = Field(None, description="Description")
    occasion: Optional[str] = Field(None, max_length=100, description="Occasion")
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    style: Optional[str] = Field(None, max_length=100, description="Style")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating")
    is_public: bool = Field(False, description="Public flag")


class OutfitCreate(OutfitBase):
    """Create outfit with items."""
    clothing_items: List[OutfitItemCreate] = Field([], description="Clothing slots")
    cover_image_url: Optional[str] = Field(None, description="Cover image URL")


class OutfitUpdate(BaseModel):
    """Partial outfit update."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    occasion: Optional[str] = Field(None, max_length=100)
    season: Optional[List[ClothingSeason]] = Field(None, description="Seasons")
    style: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = None
    wear_count: Optional[int] = Field(None, ge=0)
    last_worn_date: Optional[date] = None


class Outfit(OutfitBase):
    """Full outfit row."""
    id: int
    user_id: int
    cover_image_url: Optional[str] = None
    wear_count: int = Field(0, description="Times worn")
    last_worn_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    clothing_items: List[OutfitItem] = Field([], description="Clothing slots")

    model_config = ConfigDict(from_attributes=True)

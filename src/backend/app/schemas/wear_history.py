from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class WearHistoryBase(BaseModel):
    """Shared wear-history fields."""
    wear_date: date = Field(..., description="Date worn")
    weather: Optional[str] = Field(None, max_length=100, description="Weather text")
    temperature: Optional[int] = Field(None, description="Temperature")
    location: Optional[str] = Field(None, max_length=200, description="Location")
    occasion: Optional[str] = Field(None, max_length=100, description="Occasion")
    notes: Optional[str] = Field(None, description="Notes")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")

    @validator('wear_date')
    def wear_date_not_future(cls, v):
        """Disallow future dates."""
        if v > date.today():
            raise ValueError('Wear date cannot be in the future.')
        return v


class WearHistoryCreate(WearHistoryBase):
    """Create wear history."""
    clothing_id: Optional[int] = Field(None, description="Clothing item id")
    outfit_id: Optional[int] = Field(None, description="Outfit id when logging a full outfit")


class WearHistory(WearHistoryBase):
    """Full wear-history row."""
    id: int
    user_id: int
    clothing_id: Optional[int] = None
    outfit_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarOutfitItem(BaseModel):
    """Single calendar slot item (fields aligned with MyCalendar)."""
    id: int = Field(..., description="Clothing id from wardrobe")
    name: Optional[str] = Field(None, description="Display name (optional)")
    image: Optional[str] = Field(None, description="Image URL (optional)")
    accentColor: Optional[str] = Field(None, description="Accent for UI (optional)")


class CalendarOutfitSave(BaseModel):
    """Replace all items for one calendar day."""
    date: str = Field(..., description="YYYY-MM-DD")
    items: List[CalendarOutfitItem] = Field(
        default_factory=list,
        description="Items for that day; empty clears the day",
    )

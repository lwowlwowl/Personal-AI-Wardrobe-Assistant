from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.clothing import ClothingItem
from app.schemas.outfit import Outfit
from app.schemas.wear_history import WearHistory


class SuccessResponse(BaseModel):
    """Generic success envelope."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error envelope."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ExportData(BaseModel):
    """Bulk export bundle."""
    clothing_items: List[ClothingItem]
    outfits: List[Outfit]
    wear_history: List[WearHistory]
    export_date: datetime = Field(default_factory=datetime.now)
    total_items: int
    total_outfits: int
    total_wears: int

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ModelPhotoBase(BaseModel):
    """Shared model-photo fields."""
    photo_name: str
    description: Optional[str] = None
    is_primary: Optional[bool] = False
    is_favorite: int = Field(0, ge=0, le=3, description="Favorite level 0-3")


class ModelPhotoCreate(ModelPhotoBase):
    """Create model photo."""
    pass


class ModelPhotoUpdate(BaseModel):
    """Update model photo."""
    photo_name: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None
    is_favorite: Optional[int] = Field(None, ge=0, le=3, description="Favorite level 0-3")


class ModelPhotoInDB(ModelPhotoBase):
    """Model photo as stored."""
    id: int
    user_id: int
    image_url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None  # bytes
    file_format: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2


class ModelPhotoResponse(BaseModel):
    """API wrapper for model photo payloads."""
    success: bool
    message: Optional[str] = None
    data: Optional[Union[ModelPhotoInDB, List[ModelPhotoInDB], dict]] = None

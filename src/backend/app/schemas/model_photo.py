from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ModelPhotoBase(BaseModel):
    """Shared model-photo fields."""
    photo_name: str
    description: Optional[str] = None
    is_primary: Optional[bool] = False


class ModelPhotoCreate(ModelPhotoBase):
    """Create model photo."""
    pass


class ModelPhotoUpdate(BaseModel):
    """Update model photo."""
    photo_name: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None


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
        orm_mode = True  # legacy Pydantic v1 compat


class ModelPhotoResponse(BaseModel):
    """API wrapper for model photo payloads."""
    success: bool
    message: Optional[str] = None
    data: Optional[Union[ModelPhotoInDB, List[ModelPhotoInDB], dict]] = None

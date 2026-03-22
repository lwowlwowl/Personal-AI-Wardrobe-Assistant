from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clothing import ClothingSeason


class OutfitItemBase(BaseModel):
    """搭配中的单件衣物模型"""
    clothing_id: int = Field(..., description="衣物ID")
    position: str = Field(..., max_length=20, description="位置：top, bottom等")
    order_index: int = Field(0, description="显示顺序")


class OutfitItemCreate(OutfitItemBase):
    """创建搭配衣物请求模型"""
    pass


class OutfitItem(OutfitItemBase):
    """搭配衣物完整模型"""
    id: int
    outfit_id: int  # 所属搭配ID

    model_config = ConfigDict(from_attributes=True)


class OutfitBase(BaseModel):
    """搭配基础模型"""
    name: str = Field(..., max_length=200, description="搭配名称")
    description: Optional[str] = Field(None, description="描述")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    style: Optional[str] = Field(None, max_length=100, description="风格")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    is_public: bool = Field(False, description="是否公开")


class OutfitCreate(OutfitBase):
    """创建搭配请求模型"""
    clothing_items: List[OutfitItemCreate] = Field([], description="衣物列表")
    cover_image_url: Optional[str] = Field(None, description="封面图URL")


class OutfitUpdate(BaseModel):
    """更新搭配请求模型"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    occasion: Optional[str] = Field(None, max_length=100)
    season: Optional[List[ClothingSeason]] = Field(None, description="季节列表")
    style: Optional[str] = Field(None, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = None
    wear_count: Optional[int] = Field(None, ge=0)  # 穿着次数
    last_worn_date: Optional[date] = None  # 最后穿着日期


class Outfit(OutfitBase):
    """搭配完整模型"""
    id: int
    user_id: int  # 所属用户ID
    cover_image_url: Optional[str] = None
    wear_count: int = Field(0, description="穿着次数")
    last_worn_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    clothing_items: List[OutfitItem] = Field([], description="衣物列表")

    model_config = ConfigDict(from_attributes=True)

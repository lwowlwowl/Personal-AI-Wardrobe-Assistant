from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class WearHistoryBase(BaseModel):
    """穿着记录基础模型"""
    wear_date: date = Field(..., description="穿着日期")
    weather: Optional[str] = Field(None, max_length=100, description="天气")
    temperature: Optional[int] = Field(None, description="温度")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    occasion: Optional[str] = Field(None, max_length=100, description="场合")
    notes: Optional[str] = Field(None, description="备注")
    rating: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")  # 1-5分

    @validator('wear_date')
    def wear_date_not_future(cls, v):
        """验证穿着日期不是未来日期"""
        if v > date.today():
            raise ValueError('穿着日期不能是未来日期')
        return v


class WearHistoryCreate(WearHistoryBase):
    """创建穿着记录请求模型"""
    clothing_id: Optional[int] = Field(None, description="衣物ID")
    outfit_id: Optional[int] = Field(None, description="搭配ID")  # 如果记录的是整套搭配


class WearHistory(WearHistoryBase):
    """穿着记录完整模型"""
    id: int
    user_id: int  # 用户ID
    clothing_id: Optional[int] = None
    outfit_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarOutfitItem(BaseModel):
    """日历中的单个穿搭单品（与前端 MyCalendar 保持字段一致）"""
    id: int = Field(..., description="单品 id（对应衣橱中的 clothing_id）")
    name: Optional[str] = Field(None, description="单品名称（可选）")
    image: Optional[str] = Field(None, description="图片 URL（可选）")
    accentColor: Optional[str] = Field(None, description="主题色（前端展示用，可选）")


class CalendarOutfitSave(BaseModel):
    """保存 / 更新某天日历穿搭记录的请求体"""
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    items: List[CalendarOutfitItem] = Field(default_factory=list, description="当日穿搭单品数组（可为空数组表示清空）")

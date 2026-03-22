from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.clothing import ClothingItem
from app.schemas.outfit import Outfit
from app.schemas.wear_history import WearHistory


class SuccessResponse(BaseModel):
    """成功响应通用模型"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None  # 响应数据


class ErrorResponse(BaseModel):
    """错误响应通用模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None  # 错误代码
    details: Optional[Dict[str, Any]] = None  # 错误详情


class ExportData(BaseModel):
    """数据导出模型"""
    clothing_items: List[ClothingItem]  # 衣物列表
    outfits: List[Outfit]  # 搭配列表
    wear_history: List[WearHistory]  # 穿着记录
    export_date: datetime = Field(default_factory=datetime.now)  # 导出时间
    total_items: int  # 总衣物数
    total_outfits: int  # 总搭配数
    total_wears: int  # 总穿着次数

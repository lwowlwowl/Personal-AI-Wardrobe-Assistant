from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel


class ModelPhotoBase(BaseModel):
    """模特照片基础模型"""
    photo_name: str  # 照片名称
    description: Optional[str] = None  # 描述
    is_primary: Optional[bool] = False  # 是否为主照片


class ModelPhotoCreate(ModelPhotoBase):
    """创建模特照片请求模型"""
    pass


class ModelPhotoUpdate(BaseModel):
    """更新模特照片请求模型"""
    photo_name: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None


class ModelPhotoInDB(ModelPhotoBase):
    """模特照片数据库模型"""
    id: int
    user_id: int  # 所属用户ID
    image_url: str  # 图片URL
    thumbnail_url: Optional[str] = None  # 缩略图URL
    file_size: Optional[int] = None  # 文件大小（字节）
    file_format: Optional[str] = None  # 文件格式
    is_active: bool  # 是否激活
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # 兼容旧版Pydantic


class ModelPhotoResponse(BaseModel):
    """模特照片响应模型"""
    success: bool
    message: Optional[str] = None
    data: Optional[Union[ModelPhotoInDB, List[ModelPhotoInDB], dict]] = None

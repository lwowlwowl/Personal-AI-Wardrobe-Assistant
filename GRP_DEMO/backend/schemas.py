# schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re

# ============ 用户相关 ============
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")

class UserCreate(UserBase):
    """用户注册模型"""
    password: str = Field(..., min_length=6, max_length=72, description="密码（最大72字符）")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('username')
    def validate_username(cls, v):
        # 用户名只能包含字母、数字、下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v
    
    @validator('password')
    def validate_password_length(cls, v):
        # bcrypt 最大支持72字节，中文字符算3字节
        if len(v.encode('utf-8')) > 72:
            raise ValueError('密码过长（包含中文字符时请缩短密码）')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=6, description="密码")
    remember: bool = Field(False, description="记住我")

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # 替换原来的 orm_mode

class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

# ============ 密码重置相关 ============
class PasswordReset(BaseModel):
    """密码重置模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v

class ForgotPassword(BaseModel):
    """忘记密码请求模型"""
    email: EmailStr = Field(..., description="注册邮箱")

# ============ Token相关 ============
class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str

class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None

# ============ 衣物相关（根据你的需求添加） ============
class ClothingItemBase(BaseModel):
    """衣物基础模型"""
    name: str = Field(..., max_length=100, description="衣物名称")
    category: str = Field(..., description="衣物类别")
    color: str = Field(..., description="颜色")
    size: str = Field(..., description="尺寸")
    brand: Optional[str] = Field(None, description="品牌")
    material: Optional[str] = Field(None, description="材质")
    season: Optional[str] = Field(None, description="适用季节")
    description: Optional[str] = Field(None, description="描述")
    image_url: Optional[str] = Field(None, description="图片URL")

class ClothingItemCreate(ClothingItemBase):
    """创建衣物模型"""
    pass

class ClothingItemUpdate(BaseModel):
    """更新衣物模型"""
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    brand: Optional[str] = None
    material: Optional[str] = None
    season: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class ClothingItemResponse(ClothingItemBase):
    """衣物响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ============ 搭配相关 ============
class OutfitBase(BaseModel):
    """搭配基础模型"""
    name: str = Field(..., max_length=100, description="搭配名称")
    description: Optional[str] = Field(None, description="搭配描述")
    occasion: Optional[str] = Field(None, description="适用场合")
    weather: Optional[str] = Field(None, description="适用天气")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")

class OutfitCreate(OutfitBase):
    """创建搭配模型"""
    clothing_items: list[int] = Field(..., description="包含的衣物ID列表")

class OutfitResponse(OutfitBase):
    """搭配响应模型"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ============ API响应通用模型 ============
class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('密码至少需要6个字符')
        # 可以添加更多密码强度验证
        # if not any(char.isdigit() for char in v):
        #     raise ValueError('密码必须包含至少一个数字')
        return v


class UserLogin(BaseModel):
    username: str
    password: str
    remember: bool = False

    @validator('username')
    def username_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('密码不能为空')
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    expires_in: Optional[int] = None
    remember: Optional[bool] = None


# 新增：Token数据模型
class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


# 新增：Token响应模型
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str


# 新增：修改用户信息
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[str] = None
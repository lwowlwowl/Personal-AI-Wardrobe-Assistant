from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """用户基础模型，包含用户基本信息"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """用户创建请求模型，包含密码验证逻辑"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")

    @validator('username')
    def username_chars(cls, v):
        """Trim ends; allow Unicode letters, digits, and spaces (no other symbols)."""
        s = (v or "").strip()
        if len(s) < 3:
            raise ValueError(
                "Username must be at least 3 characters (leading/trailing spaces are ignored)."
            )
        for ch in s:
            if ch == " ":
                continue
            if not ch.isalnum():
                raise ValueError(
                    "Username may only contain letters, numbers, and spaces."
                )
        return s

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证两次输入的密码是否一致"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match.')
        return v

    @validator('password')
    def password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters.')
        return v


class UserResponse(BaseModel):
    """用户信息响应模型（返回给客户端的数据）"""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从ORM对象转换


class UserUpdate(BaseModel):
    """用户信息更新模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None  # 全名
    avatar_url: Optional[str] = None  # 头像URL

    @validator("username")
    def username_chars_optional(cls, v):
        if v is None:
            return v
        s = v.strip()
        if not s:
            return None
        if len(s) < 3:
            raise ValueError(
                "Username must be at least 3 characters (leading/trailing spaces are ignored)."
            )
        for ch in s:
            if ch == " ":
                continue
            if not ch.isalnum():
                raise ValueError(
                    "Username may only contain letters, numbers, and spaces."
                )
        return s

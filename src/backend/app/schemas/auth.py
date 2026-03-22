from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str
    remember: bool = False  # 是否记住登录状态

    @validator('username')
    def username_not_empty(cls, v):
        """验证用户名不为空"""
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_not_empty(cls, v):
        """验证密码不为空"""
        if not v:
            raise ValueError('密码不能为空')
        return v


class PasswordResetByIdentity(BaseModel):
    """未登录场景：凭邮箱 + 用户名匹配同一账号后重置密码（无邮件链路）"""
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=1)

    @validator('username')
    def username_strip(cls, v):
        s = (v or '').strip()
        if not s:
            raise ValueError('Username cannot be empty')
        return s

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class LoginResponse(BaseModel):
    """登录响应模型，包含认证令牌和用户信息"""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    expires_in: Optional[int] = None  # 令牌过期时间（秒）
    remember: Optional[bool] = None


class TokenData(BaseModel):
    """Token中存储的数据结构"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"  # 令牌类型，默认为bearer
    expires_in: int  # 过期时间（秒）
    user_id: int
    username: str


class PasswordChange(BaseModel):
    """修改密码（需验证当前密码）"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

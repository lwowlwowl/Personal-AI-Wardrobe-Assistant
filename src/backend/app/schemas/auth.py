from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserLogin(BaseModel):
    """Login request body."""
    username: str
    password: str
    remember: bool = False  # longer session when true

    @validator('username')
    def username_not_empty(cls, v):
        """Username required."""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty.')
        return v.strip()

    @validator('password')
    def password_not_empty(cls, v):
        """Password required."""
        if not v:
            raise ValueError('Password cannot be empty.')
        return v


class PasswordResetByIdentity(BaseModel):
    """Reset password when logged out: match email + username on same account (no email send)."""
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
    """Login success payload shape."""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    expires_in: Optional[int] = None  # seconds until expiry
    remember: Optional[bool] = None


class TokenData(BaseModel):
    """Claims stored in JWT."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class TokenResponse(BaseModel):
    """OAuth-style token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str


class PasswordChange(BaseModel):
    """Change password with current password verification."""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)

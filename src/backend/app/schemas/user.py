from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    """Registration payload with password checks."""
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    confirm_password: str = Field(..., description="Confirm password")

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
        """Ensure password and confirmation match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match.')
        return v

    @validator('password')
    def password_strength(cls, v):
        """Minimum length check."""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters.')
        return v


class UserResponse(BaseModel):
    """User row returned to clients."""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # allow ORM conversion


class UserUpdate(BaseModel):
    """Partial user profile update."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

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

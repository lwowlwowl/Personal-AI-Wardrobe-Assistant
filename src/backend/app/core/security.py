"""
Password hashing and JWT: single implementation shared by crud and APIs.
New passwords use pbkdf2_sha256; bcrypt kept for verifying legacy hashes.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    RESET_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)

_JWTError = getattr(jwt, "PyJWTError", getattr(jwt, "JWTError", Exception))

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Created token for sub={data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        print(f"create_access_token error: {e}")
        raise


def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token verified sub={payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except _JWTError as e:
        print(f"Token verification failed: {e}")
        return None


def create_password_reset_token(email: str) -> str:
    try:
        expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        to_encode = {"email": email, "exp": expire, "type": "reset"}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        print(f"create_password_reset_token error: {e}")
        raise


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except _JWTError:
        return None

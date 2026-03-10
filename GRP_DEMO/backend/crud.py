import traceback
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Tuple, Optional
from datetime import datetime, timedelta
import jwt
import secrets
import hashlib
import models

# ============ 密码加密配置 ============
# JWT配置
# 注意：在生产环境中建议从环境变量获取，开发阶段必须固定，否则重启会导致 Token 失效
SECRET_KEY = "WARDROBE_PROJECT_FIXED_SECRET_KEY_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2小时
RESET_TOKEN_EXPIRE_MINUTES = 30  # 30分钟


# ============ 密码工具函数 ============
def hash_password(password: str) -> str:
    """使用 SHA256 + salt 加密密码"""
    salt = secrets.token_hex(8)
    salted_password = password + salt
    hashed = hashlib.sha256(salted_password.encode()).hexdigest()
    return f"sha256${hashed}${salt}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != 'sha256':
            return False

        stored_hash = parts[1]
        salt = parts[2]

        salted_password = plain_password + salt
        computed_hash = hashlib.sha256(salted_password.encode()).hexdigest()

        return stored_hash == computed_hash
    except:
        return False


# ============ 用户CRUD操作 ============
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_data: dict) -> Tuple[Optional[models.User], Optional[str]]:
    try:
        # 1. 检查用户名
        if get_user_by_username(db, user_data["username"]):
            return None, "用户名已被注册"

        # 2. 检查邮箱
        if user_data.get("email") and get_user_by_email(db, user_data["email"]):
            return None, "邮箱已被注册"

        # 3. 创建对象
        db_user = models.User(
            username=user_data["username"],
            email=user_data.get("email"),
            hashed_password=hash_password(user_data["password"]),
            is_active=True,
            created_at=datetime.now(),
            full_name=user_data.get("full_name"),
            avatar_url=user_data.get("avatar_url")
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user, None
    except Exception as e:
        db.rollback()
        return None, f"创建用户失败: {str(e)}"


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[models.User], Optional[str]]:
    try:
        user = db.query(models.User).filter(
            or_(models.User.username == username, models.User.email == username)
        ).first()

        if not user or not verify_password(password, user.hashed_password):
            return None, "用户名或密码错误"

        if not user.is_active:
            return None, "账号已被禁用"

        return user, None
    except Exception as e:
        return None, str(e)


# ============ JWT Token 操作 ============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> Optional[dict]:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token已过期")
        return None
    except jwt.PyJWTError as e:  # 修复此处 AttributeError
        print(f"❌ Token验证失败: {e}")
        return None


# ============ 密码重置相关 ============
def create_password_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"email": email, "exp": expire, "type": "reset", "iat": datetime.utcnow()}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except (jwt.ExpiredSignatureError, jwt.PyJWTError):
        return None


def update_user_password(db: Session, email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    try:
        user = get_user_by_email(db, email)
        if not user: return False, "用户不存在"
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now()
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)


# ============ 其他管理函数 ============
def update_user_profile(db: Session, user_id: int, update_data: dict) -> Tuple[bool, Optional[str]]:
    try:
        user = get_user_by_id(db, user_id)
        if not user: return False, "用户不存在"
        if "full_name" in update_data: user.full_name = update_data["full_name"]
        if "avatar_url" in update_data: user.avatar_url = update_data["avatar_url"]
        user.updated_at = datetime.now()
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
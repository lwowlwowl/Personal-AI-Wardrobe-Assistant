import traceback

from sqlalchemy.orm import Session
from typing import Tuple, Optional
from datetime import datetime, timedelta
import jwt
import secrets
from passlib.context import CryptContext
import models

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置（生产环境应该从环境变量读取）
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2 hours
RESET_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ============ 用户CRUD操作 ============
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """根据用户名获取用户"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """根据邮箱获取用户"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """根据ID获取用户"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user_data: dict) -> Tuple[Optional[models.User], Optional[str]]:
    """创建新用户"""
    try:
        print(f"创建用户: {user_data}")

        # 检查用户名是否已存在
        if get_user_by_username(db, user_data["username"]):
            return None, "用户名已被注册"

        # 检查邮箱是否已存在（如果提供了邮箱）
        if user_data.get("email"):
            if get_user_by_email(db, user_data["email"]):
                return None, "邮箱已被注册"

        # 加密密码
        hashed_password = pwd_context.hash(user_data["password"])

        # 创建用户对象
        db_user = models.User(
            username=user_data["username"],
            email=user_data.get("email"),
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.now()
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        print(f"用户创建成功: {db_user.username}")
        return db_user, None

    except Exception as e:
        db.rollback()
        print(f"创建用户错误: {e}")
        return None, f"创建用户失败: {str(e)}"


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[models.User], Optional[str]]:
    """验证用户登录信息"""
    try:
        from sqlalchemy import or_

        print(f"[DEBUG] 开始验证用户: {username}")

        # 通过用户名或邮箱查找用户
        user = db.query(models.User).filter(
            or_(
                models.User.username == username,
                models.User.email == username
            )
        ).first()

        if not user:
            print(f"[DEBUG] 用户不存在: {username}")
            return None, "用户名或密码错误"

        print(f"[DEBUG] 找到用户: {user.username}, ID: {user.id}")
        print(f"[DEBUG] 数据库密码哈希: {user.hashed_password[:30]}...")

        # 使用正确的密码验证方法
        if not verify_password(password, user.hashed_password):
            print(f"[DEBUG] 密码验证失败: {username}")
            return None, "用户名或密码错误"

        print(f"[DEBUG] 认证成功: {user.username}")
        return user, None

    except Exception as e:
        print(f"[ERROR] authenticate_user错误: {traceback.format_exc()}")
        return None, f"认证过程中发生错误: {str(e)}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    try:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"创建token: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        print(f"create_access_token错误: {e}")
        raise

def verify_access_token(token: str) -> Optional[dict]:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"验证token成功: {payload.get('sub')}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token已过期")
        return None
    except jwt.JWTError as e:
        print(f"Token验证失败: {e}")
        return None


def create_password_reset_token(email: str) -> str:
    """创建密码重置令牌"""
    try:
        expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        to_encode = {"email": email, "exp": expire, "type": "reset"}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        print(f"创建重置token错误: {e}")
        raise


def verify_password_reset_token(token: str) -> Optional[str]:
    """验证密码重置令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def update_user_password(db: Session, email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """更新用户密码（用于忘记密码）"""
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False, "用户不存在"

        user.hashed_password = pwd_context.hash(new_password)
        user.updated_at = datetime.now()

        db.commit()
        print(f"密码更新成功: {email}")
        return True, None

    except Exception as e:
        db.rollback()
        print(f"更新密码错误: {e}")
        return False, f"更新密码失败: {str(e)}"

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()
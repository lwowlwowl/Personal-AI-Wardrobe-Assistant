"""用户 CRUD。"""
import traceback
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import app.models as models
from app.core.security import hash_password, verify_password

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


def update_user(db: Session, user_id: int, **kwargs) -> Optional[models.User]:
    """
    更新用户信息（仅更新传入的非空字段）
    参数: db, user_id, 以及 User 表可更新字段如 username, email, full_name, avatar_url
    返回: 更新后的用户对象，不存在则返回 None；若更新 username 且已被占用则抛出 ValueError
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if "username" in kwargs:
        new_username = (kwargs["username"] or "").strip()
        if new_username:
            existing = get_user_by_username(db, new_username)
            if existing and existing.id != user_id:
                raise ValueError("用户名已被使用")
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    修改当前用户密码（需验证当前密码）
    返回: (成功与否, 错误信息)
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False, "用户不存在"
    if not verify_password(current_password, user.hashed_password):
        return False, "当前密码错误"
    user.hashed_password = hash_password(new_password)
    db.commit()
    return True, None


def create_user(db: Session, user_data: dict) -> Tuple[Optional[models.User], Optional[str]]:
    """
    创建新用户

    参数:
        db: 数据库会话
        user_data: 用户数据字典，包含username、password、email等

    返回:
        Tuple[用户对象, 错误信息] - 成功时返回用户对象，失败时返回错误信息
    """
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
        hashed_password = hash_password(user_data["password"])

        # 创建用户对象
        db_user = models.User(
            username=user_data["username"],
            email=user_data.get("email"),
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.now()
        )

        # 保存到数据库
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
    """
    验证用户登录信息

    参数:
        db: 数据库会话
        username: 用户名或邮箱
        password: 密码

    返回:
        Tuple[用户对象, 错误信息] - 认证成功返回用户对象，失败返回错误信息
    """
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


def update_user_password(db: Session, email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    更新用户密码（用于忘记密码功能）

    参数:
        db: 数据库会话
        email: 用户邮箱
        new_password: 新密码

    返回:
        Tuple[是否成功, 错误信息]
    """
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False, "用户不存在"

        # 更新密码和修改时间
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now()

        db.commit()
        print(f"密码更新成功: {email}")
        return True, None

    except Exception as e:
        db.rollback()
        print(f"更新密码错误: {e}")
        return False, f"更新密码失败: {str(e)}"


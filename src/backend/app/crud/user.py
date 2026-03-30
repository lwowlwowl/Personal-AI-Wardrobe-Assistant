"""User CRUD."""
import traceback
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

import app.models as models
from app.core.security import hash_password, verify_password

# ============ User CRUD ============

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username."""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email."""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[models.User]:
    """
    Update user fields; only non-None passed values are applied.

    Args: db, user_id, plus updatable User fields e.g. username, email, full_name, avatar_url.
    Returns: updated user, or None if missing; ValueError if username is taken.
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if "username" in kwargs:
        new_username = (kwargs["username"] or "").strip()
        if new_username:
            existing = get_user_by_username(db, new_username)
            if existing and existing.id != user_id:
                raise ValueError("That username is already taken.")
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Change password after verifying the current one.

    Returns: (success, error_message)
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False, "User not found."
    if not verify_password(current_password, user.hashed_password):
        return False, "Current password is incorrect."
    user.hashed_password = hash_password(new_password)
    db.commit()
    return True, None


def create_user(db: Session, user_data: dict) -> Tuple[Optional[models.User], Optional[str]]:
    """
    Create a new user.

    Args:
        db: DB session
        user_data: dict with username, password, email, etc.

    Returns:
        (user, error_message) — user on success, error string on failure
    """
    try:
        print(f"create_user: username={user_data.get('username')}")

        if get_user_by_username(db, user_data["username"]):
            return None, "That username is already registered."

        if user_data.get("email"):
            if get_user_by_email(db, user_data["email"]):
                return None, "That email is already registered."

        hashed_password = hash_password(user_data["password"])

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

        print(f"create_user: success username={db_user.username}")
        return db_user, None

    except Exception as e:
        db.rollback()
        print(f"create_user error:\n{traceback.format_exc()}")
        return None, f"Could not create account: {str(e)}"


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[models.User], Optional[str]]:
    """
    Authenticate login.

    Args:
        db: DB session
        username: username or email
        password: plain password

    Returns:
        (user, error_message) — user on success
    """
    try:
        from sqlalchemy import or_

        user = db.query(models.User).filter(
            or_(
                models.User.username == username,
                models.User.email == username
            )
        ).first()

        if not user:
            return None, "Incorrect username or password."

        if not verify_password(password, user.hashed_password):
            return None, "Incorrect username or password."

        return user, None

    except Exception as e:
        print(f"authenticate_user error:\n{traceback.format_exc()}")
        return None, f"Sign-in failed: {str(e)}"


def update_user_password(db: Session, email: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Set password by email (forgot-password flow).

    Args:
        db: DB session
        email: user email
        new_password: new password

    Returns:
        (success, error_message)
    """
    try:
        user = get_user_by_email(db, email)
        if not user:
            return False, "No account uses this email."

        # For reset flow: reject reusing the current password.
        if verify_password(new_password, user.hashed_password):
            return False, "New password must be different from the current password."

        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now()

        db.commit()
        print(f"update_user_password: success email={email}")
        return True, None

    except Exception as e:
        db.rollback()
        print(f"update_user_password error:\n{traceback.format_exc()}")
        return False, f"Could not update password: {str(e)}"

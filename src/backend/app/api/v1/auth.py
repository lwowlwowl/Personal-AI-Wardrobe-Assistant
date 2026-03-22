import traceback
from datetime import timedelta

import app.crud as crud
import app.schemas as schemas
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

router = APIRouter(tags=["auth"])


@router.post("/api/auth/register")
async def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    try:
        print(f"注册请求: {user.username}")

        if not hasattr(crud, "create_user"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: create_user is missing.",
            )

        user_data = user.dict(exclude={"confirm_password"})
        db_user, error = crud.create_user(db, user_data)
        print(f"authenticate_user返回: user={db_user}, error='{error}'")

        if error:
            status_code = status.HTTP_400_BAD_REQUEST
            if "That username is already registered" in error:
                status_code = status.HTTP_409_CONFLICT
            elif "That email is already registered" in error:
                status_code = status.HTTP_409_CONFLICT

            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": error,
                    "status_code": status_code,
                },
            )

        print(f"注册成功: {db_user.username}")
        return {
            "success": True,
            "message": "Registration successful.",
            "data": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "is_active": db_user.is_active,
                "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
            },
            "status_code": status.HTTP_200_OK,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"注册错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/api/auth/login")
async def login(
    login_data: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    try:
        print(f"登录请求: username={login_data.username}")
        print(f"登录请求完整数据: {login_data.dict()}")

        if not hasattr(crud, "authenticate_user"):
            print("错误: 缺少authenticate_user函数")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: authenticate_user is missing.",
            )

        print("开始调用authenticate_user...")
        user, error = crud.authenticate_user(db, login_data.username, login_data.password)
        print(f"authenticate_user返回: user={user}, error='{error}'")

        if error:
            print(f"认证失败: {error}")
            return {
                "success": False,
                "message": error,
                "status_code": status.HTTP_401_UNAUTHORIZED,
            }
        print(f"authenticate_user返回结果: user={user}, error={error}")

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is disabled. Please contact support.",
            )

        if login_data.remember:
            access_token_expires = timedelta(days=7)
        else:
            access_token_expires = timedelta(minutes=120)

        if not hasattr(crud, "create_access_token"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: create_access_token is missing.",
            )

        access_token = crud.create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        return {
            "success": True,
            "message": "Signed in successfully.",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "expires_in": access_token_expires.total_seconds(),
            "remember": login_data.remember,
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"登录错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sign-in failed: {str(e)}",
        )


@router.post("/api/auth/reset-password-by-identity")
async def reset_password_by_identity(
    body: schemas.PasswordResetByIdentity,
    db: Session = Depends(get_db),
):
    try:
        email_norm = str(body.email).strip().lower()
        user = crud.get_user_by_username(db, body.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and username do not match our records.",
            )
        if (user.email or "").strip().lower() != email_norm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and username do not match our records.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is disabled.",
            )
        ok, err = crud.update_user_password(db, user.email, body.new_password)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=err or "Failed to reset password.",
            )
        return {"success": True, "message": "Password has been reset. You can sign in now."}
    except HTTPException:
        raise
    except Exception:
        print(f"reset_password_by_identity: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password.",
        ) from None


@router.get("/api/auth/verify")
async def verify_token(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        if not hasattr(crud, "verify_access_token"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: verify_access_token is missing.",
            )

        payload = crud.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please sign in again.",
            )

        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session. Please sign in again.",
            )

        if not hasattr(crud, "get_user_by_id"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server misconfiguration: get_user_by_id is missing.",
            )

        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is disabled.",
            )

        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"验证token错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not verify session: {str(e)}",
        )

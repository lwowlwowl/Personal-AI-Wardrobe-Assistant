from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import traceback

import models, schemas, crud
from database import engine, get_db

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal AI Wardrobe Assistant API",
    description="个人AI衣柜助手后端API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",  # HBuilderX默认端口
        "http://localhost:8080",
        "*"  # 开发阶段可以这样，生产环境要指定确切域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 健康检查 ============
@app.get("/")
async def root():
    return {
        "message": "Personal AI Wardrobe Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}


# ============ 用户认证相关 ============
@app.post("/api/auth/register")
async def register(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
):
    """用户注册（包含密码确认）"""
    try:
        print(f"注册请求: {user.username}")

        # 检查crud模块是否有create_user函数
        if not hasattr(crud, 'create_user'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少create_user函数"
            )

        # 提取用户数据（排除confirm_password）
        user_data = user.dict(exclude={'confirm_password'})

        db_user, error = crud.create_user(db, user_data)
        print(f"authenticate_user返回: user={db_user}, error='{error}'")
        if error:
            if "用户名已被注册" in error:
                status_code = status.HTTP_409_CONFLICT  # 409 Conflict
            elif "邮箱已被注册" in error:
                status_code = status.HTTP_409_CONFLICT  # 409 Conflict

            return {
                "success": False,
                "message": error,
                "status_code": status_code
            }

        print(f"注册成功: {db_user.username}")
        return {
            "success": True,
            "message": "注册成功",
            "data": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "is_active": db_user.is_active,
                "created_at": db_user.created_at.isoformat() if db_user.created_at else None
            },
            "status_code": status.HTTP_200_OK
        }

    except Exception as e:
        print(f"注册错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册时发生错误: {str(e)}"
        )


@app.post("/api/auth/login")
async def login(
        login_data: schemas.UserLogin,
        db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        print(f"登录请求: username={login_data.username}")
        print(f"登录请求完整数据: {login_data.dict()}")

        # 检查crud模块是否有authenticate_user函数
        if not hasattr(crud, 'authenticate_user'):
            print("错误: 缺少authenticate_user函数")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少authenticate_user函数"
            )

        print("开始调用authenticate_user...")
        user, error = crud.authenticate_user(db, login_data.username, login_data.password)
        print(f"authenticate_user返回: user={user}, error='{error}'")

        if error:
            # 明确打印错误信息
            print(f"认证失败: {error}")
            # 直接返回401错误，而不是抛出异常
            return {
                "success": False,
                "message": error,
                "status_code": status.HTTP_401_UNAUTHORIZED
            }
        print(f"authenticate_user返回结果: user={user}, error={error}")

        # 检查用户是否激活
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用，请联系管理员"
            )

        # 创建token - 根据remember设置过期时间
        if login_data.remember:
            # 记住我：7天有效期
            access_token_expires = timedelta(days=7)
        else:
            # 不记住：2小时有效期
            access_token_expires = timedelta(minutes=120)

        # 检查crud模块是否有create_access_token函数
        if not hasattr(crud, 'create_access_token'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少create_access_token函数"
            )

        access_token = crud.create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        return {
            "success": True,
            "message": "登录成功",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "expires_in": access_token_expires.total_seconds(),
            "remember": login_data.remember
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"登录错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录时发生错误: {str(e)}"
        )


# ============ Token验证接口 ============
@app.get("/api/auth/verify")
async def verify_token(
        token: str,
        db: Session = Depends(get_db)
):
    """验证token是否有效"""
    try:
        # 检查crud模块是否有verify_access_token函数
        if not hasattr(crud, 'verify_access_token'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少verify_access_token函数"
            )

        payload = crud.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的token"
            )

        username = payload.get("sub")
        user_id = payload.get("user_id")

        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )

        # 检查crud模块是否有get_user_by_id函数
        if not hasattr(crud, 'get_user_by_id'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少get_user_by_id函数"
            )

        # 验证用户是否存在且激活
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用"
            )

        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"验证token错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证token时发生错误: {str(e)}"
        )


# ============ 用户管理 ============
@app.get("/api/users/me", response_model=schemas.UserResponse)
async def read_users_me(
    token: str,
    db: Session = Depends(get_db)
):
    """获取当前用户信息（通过token验证）"""
    try:
        # 验证token
        payload = crud.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的token"
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token"
            )

        user = crud.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取用户信息错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息时发生错误: {str(e)}"
        )


async def get_user_by_id(
    user_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """根据ID获取用户信息（需要权限验证）"""
    try:
        # 验证请求者的token
        payload = crud.verify_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的token"
            )

        # 验证权限（这里简单实现：只能查看自己的信息）
        request_user_id = payload.get("user_id")
        if request_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他用户信息"
            )

        user = crud.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取用户信息错误详情: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息时发生错误: {str(e)}"
        )


# 忘记密码相关接口
@app.post("/api/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    """发送密码重置邮件（需要实现邮件服务）"""
    # TODO: 实现邮件发送逻辑
    return {"message": "重置密码链接已发送到邮箱"}


@app.post("/api/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """重置密码"""
    # TODO: 验证token并更新密码
    return {"message": "密码重置成功"}

# ============ 错误处理 ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return {
        "success": False,
        "message": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    error_detail = traceback.format_exc()
    print(f"未处理的异常: {error_detail}")
    return {
        "success": False,
        "message": "服务器内部错误",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
    }

if __name__ == "__main__":
    import uvicorn
    print("启动服务器: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
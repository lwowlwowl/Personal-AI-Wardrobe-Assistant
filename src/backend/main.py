"""
主应用文件：个人AI衣柜助手API
包含所有业务逻辑和路由定义
"""
import json
import statistics
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, case, Date
from datetime import datetime, date, timedelta
import traceback

# 导入自定义模块
import models, schemas, crud
from database import engine, get_db

import os
import sys
import time
import uuid
import calendar
from fastapi import UploadFile, File, Form, Query, Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from pathlib import Path as PathLib
from dateutil.relativedelta import relativedelta

from AIwardrobe.agent.react_agent import ReactAgent
from AIwardrobe.agent.classify_model import ClassificationModel
from AIwardrobe.agent.tools.agent_tools import (
    set_agent_request_user_id,
    reset_agent_request_user_id,
)
from AIwardrobe.services.weather_cache import (
    get_cached_location_by_coords,
    set_user_location_cache,
)

# ============ 路径配置 ============
# 项目根目录：.../Personal-AI-Wardrobe-Assistant
BASE_DIR = PathLib(__file__).resolve().parents[2]\
# todo
BACKEND_DIR = PathLib(__file__).resolve().parent
AIWARDROBE_DIR = BACKEND_DIR / "AIwardrobe"
if str(AIWARDROBE_DIR) not in sys.path:
    sys.path.insert(0, str(AIWARDROBE_DIR))

# 加载 .env：先 backend/.env，再 AIwardrobe/config/.env，使 QWEATHER_* 对天气接口生效
try:
    import dotenv
    for _env_path in (BACKEND_DIR / ".env", AIWARDROBE_DIR / "config" / ".env"):
        if _env_path.exists():
            dotenv.load_dotenv(_env_path, override=False)
except Exception:
    pass

UPLOAD_URL_PREFIX = "/Personal-AI-Wardrobe-Assistant/uploads"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============ 数据库初始化 ============
# 创建数据库表（如果不存在）
models.Base.metadata.create_all(bind=engine)

# ============ FastAPI应用初始化 ============
# 创建FastAPI应用实例，配置API文档信息
app = FastAPI(
    title="Personal AI Wardrobe Assistant API",
    description="个人AI衣柜助手后端API",
    version="1.0.0"
)

# ============ CORS跨域配置 ============
# 允许前端跨域请求。allow_credentials=True 时不能使用 "*"，需明确列出 origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",   # HBuilderX 默认端口
        "http://localhost:8080",
        "http://localhost:5173",   # Vite 默认
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:9000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 静态文件服务配置 ============
# 将文件上传目录挂载为静态资源，可通过HTTP直接访问
from fastapi.staticfiles import StaticFiles

app.mount(UPLOAD_URL_PREFIX, StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# ============ 健康检查接口 ============
@app.get("/")
async def root():
    """根路径：返回API基本信息"""
    return {
        "message": "Personal AI Wardrobe Assistant API",
        "version": "1.0.0",
        "docs": "/docs",  # Swagger文档地址
        "health": "/api/health"  # 健康检查地址
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口：用于监控服务状态"""
    return {"status": "healthy", "message": "API is running"}


# ============ 天气接口（基于用户经纬度，供前端 RecommendationAI 穿衣建议） ============
# 半小时内复用：GeoAPI（经纬度→location_id）、天气 API 均缓存，避免频繁调用和风
_WEATHER_CACHE_TTL_SEC = 30 * 60   # 30 分钟
_weather_cache: Dict[str, Dict[str, Any]] = {}  # key: location_id → { "response", "fetched_at" }


def _wind_scale_to_desc(scale: str) -> str:
    """将和风天气风力等级转为简短描述（如 Light Breeze）。"""
    try:
        n = int(scale or "0")
    except (ValueError, TypeError):
        return "—"
    if n <= 2:
        return "Light Breeze"
    if n <= 4:
        return "Moderate Breeze"
    if n <= 6:
        return "Strong Breeze"
    if n <= 8:
        return "Near Gale"
    if n <= 10:
        return "Gale"
    return "Storm"


@app.get("/api/weather/now")
async def get_weather_now(
    lat: float = Query(..., description="纬度"),
    lon: float = Query(..., description="经度"),
    token: Optional[str] = Query(None, description="用户认证令牌（用于按用户隔离天气地理缓存）"),
):
    """
    根据经纬度获取当前天气（和风天气 API），供前端显示温度与风力并做穿衣建议。
    同一 location_id（同城市/区县）30 分钟内复用缓存，不再调用和风 API。
    """
    host = (os.environ.get("QWEATHER_API_HOST") or "").strip().lower()
    if "api.qweather.com" in host and "qweatherapi.com" not in host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "QWEATHER_API_HOST 不能使用 api.qweather.com（会 403）。"
                "请登录 https://dev.qweather.com 控制台，在项目/认证里复制「API Host」专属域名（形如 https://xxx.def.qweatherapi.com），"
                "填到 backend/.env 的 QWEATHER_API_HOST，保存后重启后端。"
            ),
        )

    try:
        from utils.fetch_weather_json import get_location_all_by_coords, fetch_weather_json_now
    except ImportError as e:
        print(f"天气服务 ImportError: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"天气服务未配置或无法加载: {str(e)}",
        ) from e

    cache_user_id: int | str = "anonymous"
    if token:
        payload = crud.verify_access_token(token)
        if not payload or not payload.get("user_id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的token"
            )
        cache_user_id = payload["user_id"]

    # 第一步：经纬度 -> location（按 user_id 隔离地址缓存）
    location = get_cached_location_by_coords(cache_user_id, lat, lon, lang="en")
    if not location:
        try:
            location = get_location_all_by_coords(lat, lon, lang="en")
        except (RuntimeError, ValueError) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未匹配到该经纬度位置，请检查坐标",
            )
        set_user_location_cache(cache_user_id, lat, lon, location, lang="en")

    location_id = location.get("id")
    if not location_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未匹配到该经纬度位置，请检查坐标",
        )

    # 第二步：缓存 key = location_id，走 30 分钟复用
    cache_key = location_id
    now_ts = time.time()
    if cache_key in _weather_cache:
        entry = _weather_cache[cache_key]
        if now_ts - entry["fetched_at"] < _WEATHER_CACHE_TTL_SEC:
            return entry["response"]

    # 第三步：缓存 miss，用 location_id 查天气
    try:
        data = fetch_weather_json_now(location=location_id, lang="en")
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        print(f"天气接口异常: {traceback.format_exc()}")
        detail = f"天气服务异常: {str(e)}"
        if "403" in str(e):
            detail += "。和风 403 常见原因：请将 QWEATHER_API_HOST 改为控制台「API Host」中的专属域名（如 xxx.def.qweatherapi.com），勿用 api.qweather.com；或检查账户额度与 JWT 凭据。"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from e

    now = data.get("now") or {}
    temp = now.get("temp", "")
    text = now.get("text", "")
    wind_scale = now.get("windScale", "")
    wind_desc = _wind_scale_to_desc(wind_scale)

    response = {
        "temp": temp,
        "text": text,
        "windScale": wind_scale,
        "windDesc": wind_desc,
    }
    _weather_cache[cache_key] = {"response": response, "fetched_at": now_ts}
    return response


# ============ 用户认证相关接口 ============
@app.post("/api/auth/register")
async def register(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
):
    """
    用户注册接口（包含密码确认）
    参数：
        user: 用户注册信息，包含用户名、邮箱、密码和确认密码
        db: 数据库会话依赖注入
    返回：
        注册成功返回用户信息，失败返回错误详情
    """
    try:
        print(f"注册请求: {user.username}")

        # 检查crud模块是否有create_user函数
        if not hasattr(crud, 'create_user'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少create_user函数"
            )

        # 提取用户数据（排除confirm_password字段，因为它只是用于验证）
        user_data = user.dict(exclude={'confirm_password'})

        # 调用CRUD函数创建用户
        db_user, error = crud.create_user(db, user_data)
        print(f"authenticate_user返回: user={db_user}, error='{error}'")

        if error:
            # 根据错误类型设置合适的HTTP状态码
            status_code = status.HTTP_400_BAD_REQUEST
            if "用户名已被注册" in error:
                status_code = status.HTTP_409_CONFLICT  # 409 Conflict
            elif "邮箱已被注册" in error:
                status_code = status.HTTP_409_CONFLICT  # 409 Conflict

            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": error,
                    "status_code": status_code
                }
            )

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

    except HTTPException:
        raise
    except Exception as e:
        # 打印详细的错误堆栈信息便于调试
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
    """
    用户登录接口
    参数：
        login_data: 登录信息，包含用户名、密码和记住我选项
        db: 数据库会话依赖注入
    返回：
        登录成功返回JWT token和用户信息，失败返回错误
    """
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
        # 验证用户凭证
        user, error = crud.authenticate_user(db, login_data.username, login_data.password)
        print(f"authenticate_user返回: user={user}, error='{error}'")

        if error:
            # 认证失败，返回401未授权
            print(f"认证失败: {error}")
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

        # 根据"记住我"选项设置token过期时间
        if login_data.remember:
            # 记住我：7天有效期
            access_token_expires = timedelta(days=7)
        else:
            # 不记住：2小时有效期
            access_token_expires = timedelta(minutes=120)

        # 检查是否有创建token的函数
        if not hasattr(crud, 'create_access_token'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少create_access_token函数"
            )

        # 创建JWT访问令牌
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
    """
    验证JWT token是否有效
    参数：
        token: JWT访问令牌
        db: 数据库会话依赖注入
    返回：
        token有效返回用户信息，无效返回错误
    """
    try:
        # 检查验证token的函数是否存在
        if not hasattr(crud, 'verify_access_token'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="服务器配置错误：缺少verify_access_token函数"
            )

        # 验证token并获取payload
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

        # 检查获取用户的函数是否存在
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


# ============ 用户管理接口 ============
@app.get("/api/users/me", response_model=schemas.UserResponse)
async def read_users_me(
        token: str,
        db: Session = Depends(get_db)
):
    """
    获取当前登录用户信息（通过token验证）
    参数：
        token: JWT访问令牌（作为查询参数）
        db: 数据库会话依赖注入
    返回：
        当前用户的详细信息
    """
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


@app.patch("/api/users/me", response_model=schemas.UserResponse)
async def update_users_me(
        body: schemas.UserUpdate,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """更新当前登录用户信息（如 username、email、full_name、avatar_url）"""
    current_user = get_current_user(token, db)
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return current_user
    if "username" in update_data and (update_data["username"] or "").strip() == "":
        del update_data["username"]
    try:
        updated = crud.update_user(db, current_user.id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if updated is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return updated


@app.patch("/api/users/me/password")
async def change_password_me(
        body: schemas.PasswordChange,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """修改当前用户密码（需提供当前密码）"""
    current_user = get_current_user(token, db)
    ok, err = crud.change_password(
        db, current_user.id, body.current_password, body.new_password
    )
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err or "修改失败")
    return {"message": "密码已更新"}


@app.post("/api/users/me/avatar", response_model=schemas.UserResponse)
async def upload_user_avatar(
        file: UploadFile = File(...),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """上传当前用户头像，保存后更新用户的 avatar_url"""
    current_user = get_current_user(token, db)
    image_url = save_upload_file(file, current_user.id, file_type="avatar")
    crud.update_user(db, current_user.id, avatar_url=image_url)
    return crud.get_user_by_id(db, current_user.id)


async def get_user_by_id(
        user_id: int,
        token: str,
        db: Session = Depends(get_db)
):
    """
    根据ID获取用户信息（需要权限验证）
    参数：
        user_id: 要查询的用户ID
        token: 请求者的JWT令牌
        db: 数据库会话依赖注入
    返回：
        指定ID的用户信息（只能查看自己的信息）
    """
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


# 忘记密码相关接口（待实现）
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


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> models.User:
    """
    获取当前登录用户的依赖函数
    用于需要在多个接口中验证用户身份的场景
    参数：
        token: JWT访问令牌（作为查询参数）
        db: 数据库会话依赖注入
    返回：
        当前用户对象
    异常：
        各种验证失败的HTTP异常
    """
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

    return user


# ============ 文件上传配置 ============
# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def parse_season_form(season: Optional[str], allow_empty: bool = False) -> Optional[List[str]]:
    if not season:
        return None
    return json.loads(season)


def save_upload_file(file: UploadFile, user_id: int, file_type: str = "clothing") -> str:
    """
    保存上传的文件到服务器
    参数：
        file: FastAPI的UploadFile对象
        user_id: 用户ID，用于创建用户专属目录
        file_type: 文件类型，用于生成文件名前缀
    返回：
        文件的HTTP访问URL
    异常：
        文件类型或大小不符合要求时抛出HTTP异常
    """
    # 验证文件扩展名
    file_ext = PathLib(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，请上传 {', '.join(ALLOWED_EXTENSIONS)} 格式的图片"
        )

    # 验证文件大小
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小不能超过 {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # 生成唯一文件名，添加类型前缀
    prefix_map = {
        "clothing": "clothing_",
        "model": "model_",
        "outfit": "outfit_",
        "avatar": "avatar_"
    }
    prefix = prefix_map.get(file_type, "")

    # 使用UUID生成唯一文件名
    unique_filename = f"{prefix}{uuid.uuid4().hex}{file_ext}"
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)

    file_path = user_dir / unique_filename

    # 保存文件到磁盘
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # 返回HTTP可访问的URL路径
    return f"{UPLOAD_URL_PREFIX}/{user_id}/{unique_filename}"


def delete_file(file_url: str) -> bool:
    """
    删除服务器上的文件
    参数：
        file_url: 文件的HTTP URL
    返回：
        是否成功删除
    """
    if file_url.startswith(f"{UPLOAD_URL_PREFIX}/"):
        relative_path = file_url[len(UPLOAD_URL_PREFIX) + 1:]
        file_path = UPLOAD_DIR / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
    return False


# ============ 服装管理API ============
def _normalize_category(category: Optional[str]) -> str:
    """
    将传入的 category 规范为后端 ClothingCategory 枚举值字符串。
    - 空值 → "other"
    - 非法值 → "other"
    - 合法值：top/bottom/dress/outerwear/footwear/accessory/bag/underwear/other
    """
    if not category or not category.strip():
        return "other"
    key = category.strip().lower()
    allowed = {c.value for c in models.ClothingCategory}
    return key if key in allowed else "other"


def _normalize_season(season: Optional[str]) -> Optional[str]:
    """将前端传来的 season 规范为后端 ClothingSeason 枚举值（小写）。"""
    if not season or not season.strip():
        return None
    s = season.strip().lower()
    if s in ("spring", "summer", "autumn", "winter", "all_season"):
        return s
    return None


@app.post("/api/clothing/upload")
async def upload_clothing_item(
        file: UploadFile = File(...),
        name: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        subcategory: Optional[str] = Form(None),
        style: Optional[str] = Form(None),
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        color_code: Optional[str] = Form(None),
        pattern: Optional[str] = Form(None),
        occasion: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),  # 以逗号分隔的标签字符串
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        auto_label: bool = Form(True),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    上传衣物图片并创建衣物记录
    参数：
        file: 衣物图片文件
        name: 衣物名称
        category: 衣物分类
        color: 颜色（可选）
        season: 适用季节（可选）
        brand: 品牌（可选）
        tags: 标签，逗号分隔（可选）
        description: 描述（可选）
        price: 价格（可选）
        purchase_date: 购买日期，YYYY-MM-DD格式（可选）
        token: 用户认证令牌
        db: 数据库会话
    返回：
        上传成功的衣物信息
    """
    try:
        # 验证用户
        current_user = get_current_user(token, db)

        # 保存图片文件
        image_url = save_upload_file(file, current_user.id)
        relative_path = image_url[len(UPLOAD_URL_PREFIX) + 1:]
        local_image_path = (UPLOAD_DIR / relative_path).resolve()

        # 解析标签字符串为列表
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        season_list = parse_season_form(season, allow_empty=False) if season is not None else None

        # 解析购买日期字符串为date对象
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = date.fromisoformat(purchase_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="购买日期格式错误，请使用YYYY-MM-DD格式"
                )

        label_result: Optional[Dict[str, Any]] = None
        if auto_label:
            try:
                raw_result = ClassificationModel().execute(path=str(local_image_path))  # 这里后期可以改成batch版本的上传 能便宜
                parsed = json.loads(raw_result.strip())

                label_result = {}
                for field in ("category", "subcategory", "style", "color", "color_code", "pattern", "occasion", "description"):
                    value = parsed.get(field)
                    if value is not None and str(value).strip() != "":
                        label_result[field] = str(value).strip()

                if parsed.get("season"):
                    label_result["season"] = parsed.get("season")
                label_result["_raw"] = parsed
            except Exception as e:
                if not category:
                    delete_file(image_url)
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"图片自动打标失败: {str(e)}"
                    )

        resolved = {
            "name": name,
            "description": description,
            "category": category,
            "subcategory": subcategory,
            "style": style,
            "color": color,
            "color_code": color_code,
            "pattern": pattern,
            "season": season_list,
            "occasion": occasion,
            "brand": brand,
            "price": price,
            "purchase_date": purchase_date_obj,
            "tags": tag_list,
        }

        if label_result:
            for field in ("category", "subcategory", "style", "color", "color_code", "pattern", "occasion", "description"):
                if not resolved.get(field) and label_result.get(field):
                    resolved[field] = label_result[field]
            if resolved["season"] is None and label_result.get("season"):
                resolved["season"] = label_result["season"]

            if not resolved["tags"]:
                ai_tags = []
                for tag_field in ("subcategory", "style", "occasion", "pattern"):
                    val = label_result.get(tag_field)
                    if val:
                        ai_tags.append(str(val))
                resolved["tags"] = ai_tags

        if not resolved["category"]:
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少 category，且自动打标未返回可用分类"
            )
        resolved["category"] = _normalize_category(resolved["category"])
        if not resolved["name"]:
            fallback_name = resolved.get("subcategory") or resolved["category"]
            resolved["name"] = str(fallback_name)

        item_in = schemas.ClothingItemCreate(**resolved)

        # 创建衣物记录
        clothing_item, error = crud.clothing_crud.create_clothing_item(
            db=db,
            user_id=current_user.id,
            item_in=item_in,
            image_url=image_url,
            thumbnail_url=None  # 可以后续添加缩略图生成功能
        )

        if error:
            # 如果创建失败，删除已上传的图片
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "衣物上传成功",
            "data": {
                "id": clothing_item.id,
                "name": clothing_item.name,
                "image_url": clothing_item.image_url,
                "created_at": clothing_item.created_at.isoformat(),
                "auto_label": label_result["_raw"] if label_result else None,
                "tags": resolved.get("tags") or [],
            }
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"上传衣物错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传衣物时发生错误: {str(e)}"
        )


@app.get("/api/clothing")
async def get_clothing_items(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        category: Optional[str] = Query(None, description="分类筛选"),
        season: Optional[str] = Query(None, description="季节筛选"),
        color: Optional[str] = Query(None, description="颜色筛选"),
        brand: Optional[str] = Query(None, description="品牌筛选"),
        is_favorite: Optional[str] = Query(None, description="收藏等级筛选，支持逗号分隔多选如 0,1,2"),
        min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
        max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        order_by: str = Query("created_at", description="排序字段"),
        order_desc: bool = Query(True, description="是否降序")
):
    """
    获取用户的衣物列表（支持分页、筛选、搜索）
    参数：
        token: 用户认证令牌
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页数量，最大100
        category: 按分类筛选
        season: 按季节筛选
        color: 按颜色筛选
        brand: 按品牌筛选
        is_favorite: 按收藏状态筛选
        min_price: 最低价格筛选
        max_price: 最高价格筛选
        search: 搜索关键词（模糊匹配名称和描述）
        order_by: 排序字段
        order_desc: 是否降序排列
    返回：
        分页的衣物列表
    """
    try:
        current_user = get_current_user(token, db)

        # 解析 is_favorite：支持 "0,1,2" 或 "1" 格式
        is_favorite_parsed = None
        if is_favorite:
            try:
                levels = [int(x.strip()) for x in is_favorite.split(",") if x.strip()]
                levels = [x for x in levels if 0 <= x <= 3]
                if levels:
                    is_favorite_parsed = levels
            except ValueError:
                pass

        # 计算分页偏移量
        skip = (page - 1) * page_size

        # 调用CRUD函数获取衣物列表
        items, total = crud.clothing_crud.get_clothing_items(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            category=category,
            season=season,
            color=color,
            brand=brand,
            is_favorite=is_favorite_parsed,
            min_price=min_price,
            max_price=max_price,
            search=search,
            order_by=order_by,
            order_desc=order_desc
        )

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }

    except Exception as e:
        print(f"获取衣物列表错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物列表时发生错误: {str(e)}"
        )


@app.get("/api/clothing/{clothing_id}")
async def get_clothing_detail(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取单件衣物的详细信息
    参数：
        clothing_id: 衣物ID，路径参数
        token: 用户认证令牌
        db: 数据库会话
    返回：
        衣物的完整详细信息
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权并获取衣物
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 刷新对象以加载关联的标签等延迟加载属性
        db.refresh(item)

        return {
            "success": True,
            "data": item
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取衣物详情错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物详情时发生错误: {str(e)}"
        )


@app.put("/api/clothing/{clothing_id}")
async def update_clothing_item(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        name: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        subcategory: Optional[str] = Form(None),
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        is_favorite: Optional[str] = Form(None),
        condition: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    更新衣物信息
    参数：
        clothing_id: 要更新的衣物ID
        token: 用户认证令牌
        db: 数据库会话
        name: 新名称（可选）
        category: 新主分类（可选，后端 9 个枚举之一）
        subcategory: 新子分类（可选，用户自定义）
        color: 新颜色（可选）
        season: 新季节（可选）
        brand: 新品牌（可选）
        tags: 新标签（可选）
        description: 新描述（可选）
        price: 新价格（可选）
        purchase_date: 新购买日期（可选）
        is_favorite: 收藏状态（可选）
        condition: 衣物状况（可选）
        file: 新图片文件（可选）
    返回：
        更新后的衣物信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取衣物并验证所有权
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 更新图片（如果有新图片）
        image_url = item.image_url
        if file:
            # 删除旧图片
            delete_file(item.image_url)
            # 保存新图片
            image_url = save_upload_file(file, current_user.id)

        # 解析标签字符串为列表
        tag_list = None
        if tags is not None:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        season_list = parse_season_form(season, allow_empty=True) if season is not None else None

        # 解析 is_favorite：0-3 整数
        is_favorite_val = None
        if is_favorite is not None and is_favorite.strip():
            try:
                v = int(is_favorite.strip())
                if 0 <= v <= 3:
                    is_favorite_val = v
            except ValueError:
                pass

        # 解析购买日期字符串为date对象
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = date.fromisoformat(purchase_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="购买日期格式错误，请使用YYYY-MM-DD格式"
                )

        # 构建更新数据对象
        update_data = schemas.ClothingItemUpdate(
            name=name,
            description=description,
            category=_normalize_category(category) if category is not None else None,
            subcategory=subcategory,
            color=color,
            season=season_list,
            brand=brand,
            price=price,
            purchase_date=purchase_date_obj,
            is_favorite=is_favorite_val,
            condition=condition,
            tags=tag_list
        )

        # 更新衣物信息
        updated_item, error = crud.clothing_crud.update_clothing_item(
            db=db,
            db_item=item,
            item_in=update_data
        )

        if error:
            # 如果更新失败且上传了新图片，删除新图片
            if file:
                delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "衣物更新成功",
            "data": updated_item
        }

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新衣物错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新衣物时发生错误: {str(e)}"
        )


@app.delete("/api/clothing/{clothing_id}")
async def delete_clothing_item(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    删除衣物
    参数：
        clothing_id: 要删除的衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        删除成功信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取衣物信息（用于后续删除图片文件）
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 删除衣物记录（会级联删除相关标签等）
        success, error = crud.clothing_crud.delete_clothing_item(
            db=db,
            clothing_id=clothing_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 删除图片文件
        delete_file(item.image_url)
        if item.thumbnail_url:
            delete_file(item.thumbnail_url)

        return {
            "success": True,
            "message": "衣物删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"删除衣物错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除衣物时发生错误: {str(e)}"
        )


@app.post("/api/clothing/{clothing_id}/toggle-favorite")
async def toggle_favorite(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    切换衣物的收藏状态
    参数：
        clothing_id: 衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的收藏状态
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 切换收藏等级：0->1->2->3->0 循环
        current = int(item.is_favorite) if item.is_favorite is not None else 0
        next_val = (current + 1) % 4
        update_data = schemas.ClothingItemUpdate(is_favorite=next_val)

        updated_item, error = crud.clothing_crud.update_clothing_item(
            db=db,
            db_item=item,
            item_in=update_data
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": f"已{'取消' if next_val == 0 else '设置'}收藏",
            "data": {
                "is_favorite": updated_item.is_favorite
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"切换收藏状态错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换收藏状态时发生错误: {str(e)}"
        )


@app.post("/api/clothing/{clothing_id}/record-wear")
async def record_clothing_wear(
        clothing_id: int = Path(..., ge=1, description="衣物ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    记录衣物穿着（增加穿着次数并更新最后穿着日期）
    参数：
        clothing_id: 衣物ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的穿着统计信息
    """
    try:
        current_user = get_current_user(token, db)

        # 验证衣物所有权
        item = crud.clothing_crud.get_clothing_item_by_user(
            db=db,
            user_id=current_user.id,
            clothing_id=clothing_id
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="衣物不存在或无权访问"
            )

        # 记录穿着（增加穿着次数，更新最后穿着日期为今天）
        updated_item, error = crud.clothing_crud.record_clothing_wear(
            db=db,
            clothing_id=clothing_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "穿着记录已更新",
            "data": {
                "wear_count": updated_item.wear_count,
                "last_worn_date": updated_item.last_worn_date
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"记录穿着错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录穿着时发生错误: {str(e)}"
        )


# ============ 日历穿搭记录 API ============


@app.get("/api/calendar/outfits")
async def get_calendar_outfits(
        token: str = Query(..., description="用户认证令牌"),
        year: int = Query(..., description="年份，例如 2025"),
        month: int = Query(..., ge=1, le=12, description="月份，1-12")
        , db: Session = Depends(get_db)
):
    """
    获取指定月份的穿搭记录（供 MyCalendar 使用）
    响应结构遵循 MY_CALENDAR.md：
    {
      success: true,
      message: "Success",
      data: { outfits: { "YYYY-MM-DD": [items] } },
      status_code: 200
    }
    """
    try:
        current_user = get_current_user(token, db)

        try:
            # 计算当月第一天和最后一天
            first_day = date(year, month, 1)
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = date(year, month, last_day_num)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请求参数错误"
            )

        # 查询当前用户在该月份的穿着记录（按衣物维度）
        # 仅统计有 clothing_id 的记录，忽略 outfit_id 为主的记录
        histories = (
            db.query(models.WearHistory, models.ClothingItem)
            .join(models.ClothingItem, models.WearHistory.clothing_id == models.ClothingItem.id)
            .filter(
                models.WearHistory.user_id == current_user.id,
                models.WearHistory.wear_date >= first_day,
                models.WearHistory.wear_date <= last_day,
                models.WearHistory.clothing_id.isnot(None)
            )
            .all()
        )

        outfits: Dict[str, List[Dict[str, Any]]] = {}
        unique_ids: set = set()

        for history, clothing in histories:
            date_key = history.wear_date.strftime("%Y-%m-%d")
            image_url = clothing.image_url or ""
            item = {
                "id": clothing.id,
                "name": clothing.name,
                # 前端会按需补全为完整 URL，这里只返回后端存储的路径
                "image": image_url,
                # 可选字段：目前直接复用 clothing.color（如有需要前端可转为 accentColor）
                "accentColor": None,
            }
            outfits.setdefault(date_key, []).append(item)
            if clothing.id is not None:
                unique_ids.add(clothing.id)

        # 统计字段（可选，前端也会自行计算）
        days_recorded = sum(1 for items in outfits.values() if items)

        data = {
            "outfits": outfits,
            "monthStats": {
                "daysRecorded": days_recorded,
                "uniqueItems": len(unique_ids),
            },
        }

        return {
            "success": True,
            "message": "Success",
            "data": data,
            "status_code": 200,
        }

    except HTTPException:
        raise
    except Exception:
        print(f"获取日历穿搭记录错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )


@app.post("/api/calendar/outfits")
async def save_calendar_outfits(
        payload: schemas.CalendarOutfitSave,
        token: str = Query(..., description="用户认证令牌"),
        db: Session = Depends(get_db)
):
    """
    保存 / 更新 / 删除某天的穿搭记录（全量覆盖）
    - items 为空数组表示删除该日期记录
    """
    try:
        current_user = get_current_user(token, db)

        # 校验日期
        try:
            wear_date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="日期格式不正确"
            )

        # 校验 items
        if payload.items is None or not isinstance(payload.items, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="items 必须为数组"
            )

        clothing_ids = [item.id for item in payload.items if item.id is not None]
        if len(clothing_ids) != len(payload.items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="单品 id 不能为空"
            )

        # 校验衣物归属
        if clothing_ids:
            clothing_list = db.query(models.ClothingItem).filter(
                models.ClothingItem.user_id == current_user.id,
                models.ClothingItem.id.in_(clothing_ids)
            ).all()
            owned_ids = {c.id for c in clothing_list}
            missing_ids = [cid for cid in clothing_ids if cid not in owned_ids]
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="衣橱中不存在该单品"
                )

        # 获取当前日期已存在的穿着记录（仅 clothing_id 维度）
        existing_histories = db.query(models.WearHistory).filter(
            models.WearHistory.user_id == current_user.id,
            models.WearHistory.wear_date == wear_date,
            models.WearHistory.clothing_id.isnot(None),
            models.WearHistory.outfit_id.is_(None),
        ).all()

        existing_by_clothing = {
            h.clothing_id: h for h in existing_histories if h.clothing_id is not None
        }
        new_id_set = set(clothing_ids)

        # 1）删除不再包含的记录
        for cid, history in list(existing_by_clothing.items()):
            if cid not in new_id_set:
                db.delete(history)

        # 2）新增新的记录（使用 WearHistoryCRUD，保证 wear_count 等统计更新）
        for cid in new_id_set:
            if cid not in existing_by_clothing:
                history_in = schemas.WearHistoryCreate(
                    wear_date=wear_date,
                    clothing_id=cid,
                    outfit_id=None,
                    weather=None,
                    temperature=None,
                    location=None,
                    occasion=None,
                    notes=None,
                    rating=None,
                )
                _, error = crud.WearHistoryCRUD.create_wear_history(
                    db=db,
                    user_id=current_user.id,
                    history_in=history_in,
                )
                if error:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error
                    )

        db.commit()

        # 重新查询该日期的记录并按前端需要的结构返回
        refreshed = (
            db.query(models.WearHistory, models.ClothingItem)
            .join(models.ClothingItem, models.WearHistory.clothing_id == models.ClothingItem.id)
            .filter(
                models.WearHistory.user_id == current_user.id,
                models.WearHistory.wear_date == wear_date,
                models.WearHistory.clothing_id.isnot(None),
            )
            .all()
        )

        items: List[Dict[str, Any]] = []
        for history, clothing in refreshed:
            image_url = clothing.image_url or ""
            items.append({
                "id": clothing.id,
                "name": clothing.name,
                "image": image_url,
                "accentColor": None,
            })

        message = "Deleted" if not items else "Saved"

        return {
            "success": True,
            "message": message,
            "data": {
                "date": wear_date.strftime("%Y-%m-%d"),
                "items": items,
            },
            "status_code": 200,
        }

    except HTTPException:
        raise
    except ValidationError as e:
        # 如 wear_date 为未来日期等 Pydantic 校验错误，返回 400；去掉 "Value error, " 等前缀，只给用户看人话
        try:
            msg_list = [err.get("msg", "") for err in e.errors()]  # type: ignore[attr-defined]
            raw = "；".join([m for m in msg_list if m]) or "请求数据不合法"
            s = raw.strip()
            if s.lower().startswith("value error"):
                # 去掉 "Value error, " / "value error，" 等前缀
                rest = s[11:].lstrip(" ,，:：")
                detail = rest if rest else "请求数据不合法"
            else:
                detail = s or "请求数据不合法"
        except Exception:
            detail = "请求数据不合法"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    except Exception:
        db.rollback()
        print(f"保存日历穿搭记录错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )


# ============ 标签搜索API ============

@app.get("/api/clothing/tags/search")
async def search_by_tags(
        tag: str = Query(..., description="标签关键词"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    根据标签关键词搜索衣物（模糊匹配）
    参数：
        tag: 标签关键词
        token: 用户认证令牌
        db: 数据库会话
        page: 页码
        page_size: 每页数量
    返回：
        匹配标签的衣物列表
    """
    try:
        current_user = get_current_user(token, db)

        # 计算分页偏移量
        skip = (page - 1) * page_size

        # 直接查询标签表进行模糊匹配
        from sqlalchemy import or_

        # 构建查询：查找用户拥有的、标签包含关键词的衣物
        query = db.query(models.ClothingItem).join(
            models.ClothingTag,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingTag.tag.ilike(f"%{tag}%")  # 不区分大小写的模糊匹配
        ).distinct()  # 去重，避免同一衣物有多个匹配标签时重复出现

        total = query.count()

        # 分页查询
        items = query.offset(skip).limit(page_size).all()

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "items": items,
                "tag": tag,
                "total_count": total,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }

    except Exception as e:
        print(f"标签搜索错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标签搜索时发生错误: {str(e)}"
        )


@app.get("/api/clothing/tags/popular")
async def get_popular_tags(
        token: str = Query(...),
        db: Session = Depends(get_db),
        limit: int = Query(20, ge=1, le=50, description="返回数量")
):
    """
    获取用户最常用的标签（按使用次数排序）
    参数：
        token: 用户认证令牌
        db: 数据库会话
        limit: 返回的标签数量上限
    返回：
        热门标签列表，包含标签名和使用次数
    """
    try:
        current_user = get_current_user(token, db)

        from sqlalchemy import func

        # 查询用户最常用的标签：按标签分组，统计每个标签的出现次数，按次数降序排列
        popular_tags = db.query(
            models.ClothingTag.tag,
            func.count(models.ClothingTag.id).label("count")
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).group_by(
            models.ClothingTag.tag
        ).order_by(
            func.count(models.ClothingTag.id).desc()  # 按标签使用次数降序
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {"tag": tag.tag, "count": tag.count}
                for tag in popular_tags
            ]
        }

    except Exception as e:
        print(f"获取热门标签错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门标签时发生错误: {str(e)}"
        )


@app.get("/api/clothing/tags/all")
async def get_all_tags(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户的所有标签（去重）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        用户使用的所有不重复标签列表
    """
    try:
        current_user = get_current_user(token, db)

        # 查询用户的所有标签（去重）
        all_tags = db.query(
            models.ClothingTag.tag
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).distinct().all()  # 使用distinct确保标签不重复

        return {
            "success": True,
            "data": [tag.tag for tag in all_tags]
        }

    except Exception as e:
        print(f"获取所有标签错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取所有标签时发生错误: {str(e)}"
        )


# ============ 统计和分析API ============

@app.get("/api/clothing/stats")
async def get_clothing_stats(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户的衣物统计数据
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        衣物统计信息，如各类别数量、总价值等
    """
    try:
        current_user = get_current_user(token, db)

        # 调用CRUD函数获取统计信息
        stats = crud.clothing_crud.get_clothing_stats(
            db=db,
            user_id=current_user.id
        )

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        print(f"获取统计数据错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据时发生错误: {str(e)}"
        )


@app.get("/api/clothing/filters")
async def get_filter_options(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物筛选选项（用于前端筛选器）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        所有可用的筛选选项，如颜色、品牌、季节等
    """
    try:
        current_user = get_current_user(token, db)

        # 调用CRUD函数获取筛选选项
        filters = crud.clothing_crud.get_filter_options(
            db=db,
            user_id=current_user.id
        )

        return {
            "success": True,
            "data": filters
        }

    except Exception as e:
        print(f"获取筛选选项错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取筛选选项时发生错误: {str(e)}"
        )


class TrendDataService:
    """衣物趋势数据服务类 - 封装所有趋势相关的业务逻辑"""

    @staticmethod
    def get_date_range(view_by: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """获取时间范围"""
        now = datetime.now()

        if view_by == "yearly":
            if not start_date:
                start_date = datetime(now.year - 10, 1, 1)
            if not end_date:
                end_date = now

        elif view_by == "monthly":
            start_date = now - relativedelta(months=11)
            start_date = start_date.replace(day=1)
            end_date = now

        elif view_by == "daily":
            start_date = now - timedelta(days=29)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        else:
            raise ValueError(f"不支持的视图类型: {view_by}")

        return start_date, end_date

    @staticmethod
    def generate_time_labels(view_by: str,
                             start_date: datetime,
                             end_date: datetime) -> List[str]:
        """生成时间标签"""
        labels = []
        current = start_date

        if view_by == "yearly":
            while current.year <= end_date.year:
                labels.append(str(current.year))
                current = current.replace(year=current.year + 1)

        elif view_by == "monthly":
            while current <= end_date:
                labels.append(current.strftime("%Y-%m"))
                current += relativedelta(months=1)

        elif view_by == "daily":
            while current <= end_date:
                labels.append(current.strftime("%m/%d"))
                current += timedelta(days=1)

        return labels

    @staticmethod
    def get_time_group_field(view_by: str):
        """
        获取时间分组字段（PostgreSQL专用）
        注意：返回的是字段表达式，不是label
        """
        if view_by == "yearly":
            # 提取年份
            return func.extract('year', models.ClothingItem.created_at)
        elif view_by == "monthly":
            # 格式化为 YYYY-MM
            return func.to_char(models.ClothingItem.created_at, 'YYYY-MM')
        elif view_by == "daily":
            # 转换为日期
            return func.cast(models.ClothingItem.created_at, Date)
        else:
            return func.extract('year', models.ClothingItem.created_at)


@app.get("/api/analysis/total-items/trend")
async def get_total_items_trend(
        token: str = Query(...),
        db: Session = Depends(get_db),
        view_by: str = Query("yearly", regex="^(yearly|monthly|daily)$"),
        start_year: Optional[int] = Query(None, ge=2000, le=2100),
        end_year: Optional[int] = Query(None, ge=2000, le=2100),
        include_projection: bool = Query(True, description="是否包含预测数据")
):
    try:
        print(f"===== 收到趋势API请求 =====")
        print(f"view_by: {view_by}")

        current_user = get_current_user(token, db)

        # 初始化趋势数据服务
        trend_service = TrendDataService()

        # 获取用户最早衣物时间
        first_item = db.query(func.min(models.ClothingItem.created_at)).filter(
            models.ClothingItem.user_id == current_user.id,
        ).scalar()

        if not first_item:
            return {
                "success": True,
                "data": {
                    "labels": [],
                    "values": [],
                    "increments": [],
                    "view_by": view_by,
                    "total_count": 0,
                    "statistics": {}
                }
            }

        now = datetime.now()

        # 确定时间范围
        if view_by == "yearly":
            start_date = datetime(start_year or first_item.year, 1, 1)
            end_date = datetime(end_year or now.year, 12, 31)
        else:
            start_date, end_date = trend_service.get_date_range(view_by)

        # 获取分组字段
        group_field = trend_service.get_time_group_field(view_by)

        # 查询衣物数量（按时间分组）
        # 重要：在 group_by 和 order_by 中使用相同的表达式
        query = db.query(
            group_field.label('time_period'),
            func.count(models.ClothingItem.id).label('increment')
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.created_at.between(start_date, end_date)
        ).group_by(
            group_field  # 使用表达式，而不是label
        ).order_by(
            group_field  # 使用表达式，而不是label
        )

        results = query.all()
        print(f"查询结果: {len(results)} 条记录")

        # 生成完整的时间标签
        labels = trend_service.generate_time_labels(view_by, start_date, end_date)

        # 创建数据映射
        increment_map = {}
        for r in results:
            if view_by == "yearly":
                # extract 返回的是 Decimal，需要转换为整数
                key = str(int(r.time_period))
            elif view_by == "monthly":
                # to_char 返回的是字符串
                key = r.time_period
            else:  # daily
                # cast to Date 返回的是 date 对象
                key = r.time_period.strftime("%Y-%m-%d") if hasattr(r.time_period, 'strftime') else str(r.time_period)
            increment_map[key] = r.increment

        # 构建增量数据和累计数据
        increments = []
        cumulative_values = []
        total = 0

        # 获取历史累计基数
        base_count = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.created_at < start_date
        ).scalar() or 0
        total = base_count

        for label in labels:
            if view_by == "yearly":
                key = label
            elif view_by == "monthly":
                key = label
            else:  # daily
                # 将 "MM/DD" 格式转换为日期键
                try:
                    month, day = map(int, label.split('/'))
                    year = start_date.year
                    if month == 1 and start_date.month == 12:
                        year = end_date.year
                    date_key = datetime(year, month, day).strftime("%Y-%m-%d")
                    key = date_key
                except:
                    key = label

            increment = increment_map.get(key, 0)
            increments.append(increment)
            total += increment
            cumulative_values.append(total)

        # 计算统计指标
        statistics = {}
        if cumulative_values:
            # 平均增长率
            if len(cumulative_values) > 1:
                growth_rates = []
                for i in range(1, len(cumulative_values)):
                    if cumulative_values[i - 1] > 0:
                        rate = (cumulative_values[i] - cumulative_values[i - 1]) / cumulative_values[i - 1] * 100
                        growth_rates.append(rate)
                statistics['avg_growth'] = round(sum(growth_rates) / len(growth_rates), 2) if growth_rates else 0
            else:
                statistics['avg_growth'] = 0

            # 最大增长
            if increments:
                max_growth = max(increments)
                max_index = increments.index(max_growth)
                statistics['max_growth'] = max_growth
                statistics['max_period'] = labels[max_index] if max_index < len(labels) else None

            # 预测数据
            if include_projection and view_by == "yearly" and len(cumulative_values) >= 3:
                x = list(range(len(cumulative_values)))
                y = cumulative_values

                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_xx = sum(x[i] * x[i] for i in range(n))

                if n * sum_xx - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                    intercept = (sum_y - slope * sum_x) / n

                    next_year = len(cumulative_values)
                    projection = slope * next_year + intercept
                    statistics['projection'] = round(projection)

                    last_year = int(labels[-1]) if labels else now.year
                    statistics['projection_year'] = last_year + 1

        return {
            "success": True,
            "data": {
                "labels": labels,
                "values": cumulative_values,
                "increments": increments,
                "view_by": view_by,
                "total_count": cumulative_values[-1] if cumulative_values else 0,
                "statistics": statistics,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取衣物趋势数据错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物趋势数据时发生错误: {str(e)}"
        )


@app.get("/api/analysis/total-items/summary")
async def get_total_items_summary(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物总数概览信息（使用简单查询）
    """
    try:
        current_user = get_current_user(token, db)

        now = datetime.now()

        # 时间范围定义
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # 上月同期
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_end = month_start - timedelta(days=1)

        # 基础查询
        base_query = db.query(models.ClothingItem).filter(
            models.ClothingItem.user_id == current_user.id,
        )

        # 分别查询各个统计数据
        total_items = base_query.count()
        total_value = db.query(func.sum(models.ClothingItem.price)).filter(
            models.ClothingItem.user_id == current_user.id,
        ).scalar() or 0

        categories_count = db.query(func.count(func.distinct(models.ClothingItem.category))).filter(
            models.ClothingItem.user_id == current_user.id,
        ).scalar() or 0

        # 今日新增
        today_new = base_query.filter(models.ClothingItem.created_at >= today_start).count()

        # 本周新增
        week_new = base_query.filter(models.ClothingItem.created_at >= week_start).count()

        # 本月新增
        month_new = base_query.filter(models.ClothingItem.created_at >= month_start).count()

        # 今年新增
        year_new = base_query.filter(models.ClothingItem.created_at >= year_start).count()

        # 上月新增
        last_month_new = base_query.filter(
            models.ClothingItem.created_at.between(last_month_start, last_month_end)
        ).count()

        # 最近添加的5件衣物
        latest_items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.created_at
        ).filter(
            models.ClothingItem.user_id == current_user.id,
        ).order_by(
            models.ClothingItem.created_at.desc()
        ).limit(5).all()

        # 计算增长率
        growth_rate = 0
        if last_month_new > 0:
            growth_rate = round(((month_new - last_month_new) / last_month_new) * 100, 1)

        return {
            "success": True,
            "data": {
                "total_items": total_items,
                "total_value": float(total_value),
                "categories_count": categories_count,
                "latest_added": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "image_url": item.image_url,
                        "created_at": item.created_at.isoformat()
                    }
                    for item in latest_items
                ],
                "growth_rate": growth_rate,
                "stats_by_period": {
                    "today": today_new,
                    "this_week": week_new,
                    "this_month": month_new,
                    "this_year": year_new
                }
            }
        }

    except Exception as e:
        print(f"获取衣物概览统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取衣物概览统计时发生错误: {str(e)}"
        )


@app.get("/api/analysis/total-items/category-distribution")
async def get_category_distribution(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取衣物分类分布数据（用于圆环图）

    返回数据格式：
    {
        "success": true,
        "data": [
            {"label": "上衣", "value": 35, "color": "#FCD568"},
            ...
        ]
    }
    """
    try:
        current_user = get_current_user(token, db)

        # 查询各分类数量
        from sqlalchemy import func

        category_counts = db.query(
            models.ClothingItem.category,
            func.count(models.ClothingItem.id).label('count')
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).group_by(
            models.ClothingItem.category
        ).order_by(
            func.count(models.ClothingItem.id).desc()
        ).all()

        # 分类颜色映射
        category_colors = {
            "top": "#FCD568",  # 上衣 - 黄色
            "bottom": "#68C5FA",  # 下装 - 蓝色
            "dress": "#FF69B4",  # 连衣裙 - 粉色
            "outerwear": "#A694F5",  # 外套 - 紫色
            "footwear": "#E57373",  # 鞋履 - 红色
            "accessory": "#4DB6AC",  # 配饰 - 青色
            "bag": "#FFB347",       # 包 - 橙色
            "underwear": "#E0E0E0", # 内衣 - 灰色
            "other": "#999999"      # 其他 - 深灰色
        }

        # 分类名称映射（用于显示）
        category_names = {
            "top": "上衣",
            "bottom": "下装",
            "dress": "连衣裙",
            "outerwear": "外套",
            "footwear": "鞋履",
            "accessory": "配饰",
            "bag": "包袋",
            "underwear": "内衣",
            "other": "其他"
        }

        # 构建返回数据
        distribution_data = []
        for cat in category_counts:
            if cat.category:  # 确保分类不为空
                distribution_data.append({
                    "label": category_names.get(cat.category, cat.category),
                    "value": cat.count,
                    "color": category_colors.get(cat.category, "#999999")
                })

        return {
            "success": True,
            "data": distribution_data
        }

    except Exception as e:
        print(f"获取分类分布错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类分布时发生错误: {str(e)}"
        )


@app.get("/api/analysis/total-items/export")
async def export_trend_data(
        token: str = Query(...),
        db: Session = Depends(get_db),
        format: str = Query("json", regex="^(json|csv)$"),
        view_by: str = Query("yearly", regex="^(yearly|monthly|daily)$"),
        start_year: Optional[int] = Query(None),
        end_year: Optional[int] = Query(None)
):
    """
    导出衣物趋势数据
    支持JSON和CSV格式
    """
    try:
        current_user = get_current_user(token, db)

        # 先获取趋势数据
        trend_response = await get_total_items_trend(
            token=token,
            db=db,
            view_by=view_by,
            start_year=start_year,
            end_year=end_year,
            include_projection=False
        )

        if not trend_response.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取趋势数据失败"
            )

        trend_data = trend_response["data"]

        if format == "csv":
            # 生成CSV格式
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            # 写入表头
            writer.writerow(["时间", "新增数量", "累计总数"])

            # 写入数据
            for i in range(len(trend_data["labels"])):
                writer.writerow([
                    trend_data["labels"][i],
                    trend_data["increments"][i],
                    trend_data["values"][i]
                ])

            # 返回CSV文件
            from fastapi.responses import Response
            filename = f"clothing_trend_{view_by}_{datetime.now().strftime('%Y%m%d')}.csv"
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON格式
            return trend_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"导出趋势数据错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出趋势数据时发生错误: {str(e)}"
        )


@app.get("/api/analysis/idle-rate")
async def get_idle_rate(
        token: str = Query(...),
        db: Session = Depends(get_db),
        days: int = Query(30, ge=1, le=365, description="闲置天数阈值")
):
    """
    获取衣物的闲置率统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
        days: 闲置天数阈值（默认30天未穿视为闲置）
    返回：
        闲置率、闲置数量、总数等信息
    """
    try:
        current_user = get_current_user(token, db)

        # 计算截止日期
        from datetime import datetime, timedelta, date  # 导入 date
        cutoff_date = datetime.now() - timedelta(days=days)
        today = date.today()

        # 1. 获取总衣物数
        total_items = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id
        ).scalar() or 0

        # 2. 获取闲置衣物数（从未穿过或最后穿着时间超过阈值）
        idle_items = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            # 满足以下任一条件视为闲置：
            # 1. wear_count为0（从未穿过）
            # 2. last_worn_date小于截止日期（超过阈值未穿）
            # 3. last_worn_date为null（从未穿过）
            (
                    (models.ClothingItem.wear_count == 0) |
                    (models.ClothingItem.last_worn_date < cutoff_date) |
                    (models.ClothingItem.last_worn_date.is_(None))
            )
        ).scalar() or 0

        # 3. 计算闲置率
        idle_rate = round((idle_items / total_items * 100), 1) if total_items > 0 else 0

        # 4. 获取最久未穿的几件衣物（用于详情页）
        most_idle_items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.image_url,
            models.ClothingItem.wear_count,
            models.ClothingItem.last_worn_date
        ).filter(
            models.ClothingItem.user_id == current_user.id,
        ).order_by(
            # 按最后穿着时间升序（最久未穿的排在前面）
            models.ClothingItem.last_worn_date.asc().nullsfirst()  # null（从未穿过）排在最前
        ).limit(10).all()

        # 构建返回数据
        most_idle_items_data = []
        for item in most_idle_items:
            days_since_last_worn = None
            if item.last_worn_date:
                # 使用 date 对象相减
                days_since_last_worn = (today - item.last_worn_date).days
            else:
                # 从未穿过，给一个较大的值
                days_since_last_worn = days * 2

            most_idle_items_data.append({
                "id": item.id,
                "name": item.name,
                "image_url": item.image_url,
                "wear_count": item.wear_count,
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
                "days_since_last_worn": days_since_last_worn
            })

        return {
            "success": True,
            "data": {
                "total_items": total_items,
                "idle_items": idle_items,
                "idle_rate": idle_rate,
                "threshold_days": days,
                "most_idle_items": most_idle_items_data
            }
        }

    except Exception as e:
        print(f"获取闲置率错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取闲置率时发生错误: {str(e)}"
        )


@app.get("/api/analysis/idle-items/detail")
async def get_idle_items_detail(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        time_filter: Optional[str] = Query(None, regex="^(never|over_year|over_six_months|over_three_months)$"),
        season_filter: Optional[str] = Query(None)
):
    """
    获取闲置物品详情列表（支持筛选）
    """
    try:
        current_user = get_current_user(token, db)

        # 计算截止日期
        from datetime import datetime, timedelta
        now = datetime.now()

        # 构建查询
        query = db.query(models.ClothingItem).filter(
            models.ClothingItem.user_id == current_user.id
        )

        # 应用时间筛选
        if time_filter == "never":
            query = query.filter(models.ClothingItem.wear_count == 0)
        elif time_filter == "over_year":
            cutoff = now - timedelta(days=365)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )
        elif time_filter == "over_six_months":
            cutoff = now - timedelta(days=180)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )
        elif time_filter == "over_three_months":
            cutoff = now - timedelta(days=90)
            query = query.filter(
                models.ClothingItem.last_worn_date < cutoff,
                models.ClothingItem.wear_count > 0
            )

        # 应用季节筛选
        if season_filter and season_filter != "all":
            query = query.filter(models.ClothingItem.season == season_filter)

        # 分页
        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(
            models.ClothingItem.last_worn_date.asc().nullsfirst()
        ).offset(skip).limit(page_size).all()

        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }

    except Exception as e:
        print(f"获取闲置物品详情错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取闲置物品详情时发生错误: {str(e)}"
        )


@app.get("/api/analysis/top-color")
async def get_top_color(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户衣柜中最常用的颜色统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        最常用颜色及其占比
    """
    try:
        current_user = get_current_user(token, db)

        # 查询用户所有衣物的颜色分布
        color_counts = db.query(
            models.ClothingItem.color,
            func.count(models.ClothingItem.id).label('count')
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.color.isnot(None)  # 排除颜色为空的记录
        ).group_by(
            models.ClothingItem.color
        ).order_by(
            func.count(models.ClothingItem.id).desc()
        ).all()

        # 计算总数
        total_items_with_color = db.query(func.count(models.ClothingItem.id)).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingItem.color.isnot(None)
        ).scalar() or 0

        # 颜色名称映射（中英文映射）
        color_name_map = {
            "white": "白色",
            "black": "黑色",
            "gray": "灰色",
            "brown": "棕色",
            "beige": "米色",
            "navy": "藏青色",
            "blue": "蓝色",
            "red": "红色",
            "green": "绿色",
            "yellow": "黄色",
            "pink": "粉色",
            "purple": "紫色",
            "orange": "橙色",
            "multicolor": "多色"
        }

        # 构建返回数据
        top_color_data = []
        for color_item in color_counts:
            top_color_data.append({
                "color_code": color_item.color,
                "color_name": color_name_map.get(color_item.color, color_item.color),
                "count": color_item.count,
                "percentage": round((color_item.count / total_items_with_color * 100),
                                    1) if total_items_with_color > 0 else 0
            })

        # 获取最常用颜色
        top_color = top_color_data[0] if top_color_data else {
            "color_code": "brown",
            "color_name": "棕色",
            "count": 0,
            "percentage": 0
        }

        return {
            "success": True,
            "data": {
                "top_color": top_color,
                "color_distribution": top_color_data,
                "total_items_with_color": total_items_with_color
            }
        }

    except Exception as e:
        print(f"获取颜色统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取颜色统计时发生错误: {str(e)}"
        )


@app.get("/api/analysis/top-style")
async def get_top_style(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户衣柜中最常用的风格统计
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        最常用风格及其占比
    """
    try:
        current_user = get_current_user(token, db)

        # 通过标签统计风格（假设风格以标签形式存储）
        style_tags = db.query(
            models.ClothingTag.tag,
            func.count(models.ClothingTag.id).label('count')
        ).join(
            models.ClothingItem,
            models.ClothingItem.id == models.ClothingTag.clothing_id
        ).filter(
            models.ClothingItem.user_id == current_user.id,
            models.ClothingTag.tag.in_([
                "sporty", "casual", "formal", "business",
                "minimal", "bohemian", "vintage", "streetwear",
                "运动", "休闲", "正式", "商务", "简约", "波西米亚", "复古", "街头"
            ])
        ).group_by(
            models.ClothingTag.tag
        ).order_by(
            func.count(models.ClothingTag.id).desc()
        ).all()

        # 风格名称映射
        style_name_map = {
            "sporty": "运动风",
            "casual": "休闲风",
            "formal": "正式风",
            "business": "商务风",
            "minimal": "简约风",
            "bohemian": "波西米亚",
            "vintage": "复古风",
            "streetwear": "街头风",
            "运动": "运动风",
            "休闲": "休闲风",
            "正式": "正式风",
            "商务": "商务风",
            "简约": "简约风",
            "波西米亚": "波西米亚",
            "复古": "复古风",
            "街头": "街头风"
        }

        # 计算总数
        total_styles = sum(item.count for item in style_tags) or 1

        # 构建返回数据
        style_data = []
        for style_item in style_tags:
            style_data.append({
                "style_code": style_item.tag,
                "style_name": style_name_map.get(style_item.tag, style_item.tag),
                "count": style_item.count,
                "percentage": round((style_item.count / total_styles * 100), 1)
            })

        # 获取最常用风格
        top_style = style_data[0] if style_data else {
            "style_code": "casual",
            "style_name": "休闲风",
            "count": 0,
            "percentage": 0
        }

        return {
            "success": True,
            "data": {
                "top_style": top_style,
                "style_distribution": style_data,
                "total_styles_count": total_styles
            }
        }

    except Exception as e:
        print(f"获取风格统计错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取风格统计时发生错误: {str(e)}"
        )


@app.get("/api/analysis/most-worn")
async def get_most_worn_items(
        token: str = Query(...),
        db: Session = Depends(get_db),
        time_range: str = Query("yearly", regex="^(yearly|monthly|daily)$"),
        limit: int = Query(5, ge=1, le=20, description="返回数量")
):
    """
    获取最常穿物品（支持时间范围筛选）
    """
    try:
        print(f"========== 收到最常穿物品请求 ==========")
        print(f"time_range: {time_range}")
        print(f"limit: {limit}")

        current_user = get_current_user(token, db)
        print(f"用户ID: {current_user.id}")

        from datetime import datetime, date, timedelta

        now = datetime.now()
        today = date.today()

        # 根据时间范围设置起始日期
        if time_range == "yearly":
            # 年度统计：从今年1月1日开始
            start_date = date(now.year, 1, 1)
            date_range_text = f"今年 ({now.year}年)"
        elif time_range == "monthly":
            # 月度统计：从本月1日开始
            start_date = date(now.year, now.month, 1)
            date_range_text = f"本月 ({now.year}年{now.month}月)"
        else:  # daily
            # 每日统计：从今天开始
            start_date = today
            date_range_text = f"今天 ({today.isoformat()})"

        print(f"统计起始日期: {start_date} ({date_range_text})")

        # 查询用户的所有衣物
        items = db.query(
            models.ClothingItem.id,
            models.ClothingItem.name,
            models.ClothingItem.color,
            models.ClothingItem.wear_count,
            models.ClothingItem.last_worn_date,
            models.ClothingItem.created_at
        ).filter(
            models.ClothingItem.user_id == current_user.id
        ).all()

        print(f"找到 {len(items)} 件衣物")

        # 如果没有衣物数据，返回空列表
        if not items:
            return {
                "success": True,
                "data": {
                    "items": [],
                    "time_range": time_range,
                    "date_range": date_range_text
                }
            }

        # 构建返回数据，计算在时间范围内的穿着次数
        most_worn_data = []

        for item in items:
            # 基础信息
            item_data = {
                "id": item.id,
                "name": item.name,
                "color": item.color or "gray",
                "total_wear_count": item.wear_count,  # 总穿着次数
                "last_worn_date": item.last_worn_date.isoformat() if item.last_worn_date else None,
            }

            # 计算在指定时间范围内的穿着次数
            wears_in_range = 0

            if item.last_worn_date:
                # 转换 last_worn_date 为 date 类型
                last_worn = item.last_worn_date
                if hasattr(last_worn, 'date'):
                    last_worn = last_worn.date()

                # 如果在时间范围内有穿着记录
                if last_worn >= start_date:
                    # 对于 yearly/monthly/daily 的不同处理
                    if time_range == "daily":
                        # 每日：如果最后穿着时间是今天，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn == today else 0
                    elif time_range == "monthly":
                        # 月度：如果最后穿着时间在本月，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn.month == now.month and last_worn.year == now.year else 0
                    else:  # yearly
                        # 年度：如果最后穿着时间在今年，显示实际穿着次数，否则为0
                        wears_in_range = item.wear_count if last_worn.year == now.year else 0
                else:
                    wears_in_range = 0
            else:
                # 从未穿过
                wears_in_range = 0

            item_data["wear_count"] = wears_in_range  # 时间范围内的穿着次数

            # 添加调试信息
            print(
                f"衣物: {item.name}, 总穿着: {item.wear_count}, 最后穿着: {item.last_worn_date}, 范围内穿着: {wears_in_range}, 时间范围: {time_range}")

            most_worn_data.append(item_data)

        # 按穿着次数排序并限制数量
        most_worn_data.sort(key=lambda x: x["wear_count"], reverse=True)
        most_worn_data = most_worn_data[:limit]

        # 格式化返回数据（保持与前端期望的格式一致）
        formatted_items = [
            {
                "name": item["name"],
                "wears": item["wear_count"],
                "color": item["color"]
            }
            for item in most_worn_data
        ]

        print(f"返回数据: {formatted_items}")

        return {
            "success": True,
            "data": {
                "items": formatted_items,
                "time_range": time_range,
                "date_range": date_range_text,
                "total_items": len(items)
            }
        }

    except Exception as e:
        print(f"获取最常穿物品错误: {traceback.format_exc()}")
        # 出错时返回模拟数据，避免前端崩溃
        return {
            "success": True,
            "data": {
                "items": [
                    {"name": "示例物品1", "wears": 10, "color": "blue"},
                    {"name": "示例物品2", "wears": 8, "color": "black"},
                    {"name": "示例物品3", "wears": 5, "color": "white"},
                ],
                "time_range": time_range,
                "note": "返回了示例数据（后端出错）"
            }
        }


# ============ 分类和枚举API ============

@app.get("/api/clothing/categories")
async def get_clothing_categories():
    """
    获取衣物分类选项（从枚举中读取）
    返回：
        所有衣物分类、子分类、季节、状况等枚举选项
    """
    try:
        # 从模型定义的枚举中获取主分类
        categories = [
            {"value": category.value, "label": category.name}
            for category in models.ClothingCategory
        ]

        # 定义子分类映射（可以根据需要扩展）
        subcategories = {
            "top": [
                {"value": "t-shirt", "label": "T恤"},
                {"value": "shirt", "label": "衬衫"},
                {"value": "sweater", "label": "毛衣"},
                {"value": "hoodie", "label": "卫衣"},
                {"value": "blouse", "label": "女士衬衫"}
            ],
            "bottom": [
                {"value": "jeans", "label": "牛仔裤"},
                {"value": "pants", "label": "裤子"},
                {"value": "shorts", "label": "短裤"},
                {"value": "skirt", "label": "半身裙"}
            ],
            "dress": [
                {"value": "summer-dress", "label": "夏季连衣裙"},
                {"value": "evening-dress", "label": "晚礼服"},
                {"value": "casual-dress", "label": "休闲裙"}
            ],
            "outerwear": [
                {"value": "jacket", "label": "夹克"},
                {"value": "coat", "label": "大衣"},
                {"value": "windbreaker", "label": "风衣"}
            ],
            "footwear": [
                {"value": "sneakers", "label": "运动鞋"},
                {"value": "shoes", "label": "皮鞋"},
                {"value": "sandals", "label": "凉鞋"},
                {"value": "boots", "label": "靴子"}
            ]
        }

        # 返回所有枚举类型，用于前端表单
        return {
            "success": True,
            "data": {
                "categories": categories,
                "subcategories": subcategories,
                "seasons": [
                    {"value": season.value, "label": season.name}
                    for season in models.ClothingSeason
                ],
                "conditions": [
                    {"value": condition.value, "label": condition.name}
                    for condition in models.ClothingCondition
                ],
                "fit_types": [
                    {"value": fit_type.value, "label": fit_type.name}
                    for fit_type in models.ClothingFitType
                ],
                "patterns": [
                    {"value": pattern.value, "label": pattern.name}
                    for pattern in models.ClothingPattern
                ]
            }
        }

    except Exception as e:
        print(f"获取分类选项错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类选项时发生错误: {str(e)}"
        )


# ============ 批量操作API ============

@app.post("/api/clothing/batch/delete")
async def batch_delete_clothing(
        clothing_ids: List[int],
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    批量删除衣物
    参数：
        clothing_ids: 要删除的衣物ID列表
        token: 用户认证令牌
        db: 数据库会话
    返回：
        批量删除结果
    """
    try:
        current_user = get_current_user(token, db)

        if not clothing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要删除的衣物"
            )

        # 获取要删除的衣物信息（用于后续删除图片文件）
        items = db.query(models.ClothingItem).filter(
            models.ClothingItem.id.in_(clothing_ids),
            models.ClothingItem.user_id == current_user.id
        ).all()

        # 验证所有衣物都存在且属于当前用户
        if len(items) != len(clothing_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分衣物不存在或无权访问"
            )

        # 执行批量删除
        deleted_count, error = crud.batch_crud.batch_delete_clothing(
            db=db,
            user_id=current_user.id,
            clothing_ids=clothing_ids
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 批量删除图片文件
        for item in items:
            delete_file(item.image_url)
            if item.thumbnail_url:
                delete_file(item.thumbnail_url)

        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 件衣物"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"批量删除错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除时发生错误: {str(e)}"
        )


@app.post("/api/clothing/batch/update")
async def batch_update_clothing(
        clothing_ids: List[int],
        update_data: Dict[str, Any],
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    批量更新衣物信息
    参数：
        clothing_ids: 要更新的衣物ID列表
        update_data: 更新数据的字典
        token: 用户认证令牌
        db: 数据库会话
    返回：
        批量更新结果
    """
    try:
        current_user = get_current_user(token, db)

        if not clothing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要更新的衣物"
            )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供更新数据"
            )

        # 执行批量更新
        updated_count, error = crud.batch_crud.batch_update_clothing(
            db=db,
            user_id=current_user.id,
            clothing_ids=clothing_ids,
            update_data=update_data
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": f"成功更新 {updated_count} 件衣物"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"批量更新错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新时发生错误: {str(e)}"
        )


# ============ 模特照片管理API ============

@app.post("/api/model-photos/upload")
async def upload_model_photo(
        file: UploadFile = File(...),
        photo_name: str = Form(...),
        description: Optional[str] = Form(None),
        is_primary: Optional[str] = Form("false"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    上传模特照片（用于虚拟试衣功能）
    参数：
        file: 模特照片文件
        photo_name: 照片名称
        description: 照片描述（可选）
        is_primary: 是否设为主要照片（表单传 "true"/"false" 字符串，需解析为 bool）
        token: 用户认证令牌
        db: 数据库会话
    返回：
        上传成功的模特照片信息
    """
    try:
        # 表单中 is_primary 为字符串 "true"/"false"，Python 中 bool("false") 为 True，需显式解析
        is_primary_bool = str(is_primary).strip().lower() in ("true", "1", "on", "yes") if is_primary else False

        # 验证用户
        current_user = get_current_user(token, db)

        # 保存图片文件（复用文件上传函数）
        image_url = save_upload_file(file, current_user.id)

        # 获取文件信息
        file_size = file.size
        file_ext = PathLib(file.filename).suffix.lower()
        file_format = file_ext[1:] if file_ext else None

        # 创建模特照片记录
        model_photo, error = crud.model_photo_crud.create_model_photo(
            db=db,
            user_id=current_user.id,
            photo_name=photo_name,
            image_url=image_url,
            description=description,
            file_size=file_size,
            file_format=file_format,
            is_primary=is_primary_bool
        )

        if error:
            # 如果创建失败，删除已上传的图片
            delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "模特照片上传成功",
            "data": model_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"上传模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传模特照片时发生错误: {str(e)}"
        )


@app.get("/api/model-photos")
async def get_model_photos(
        token: str = Query(...),
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        is_active: bool = Query(True, description="是否只显示激活的照片")
):
    """
    获取用户的模特照片列表
    参数：
        token: 用户认证令牌
        db: 数据库会话
        page: 页码
        page_size: 每页数量
        is_active: 是否只显示激活的照片（软删除标记）
    返回：
        分页的模特照片列表
    """
    try:
        current_user = get_current_user(token, db)

        skip = (page - 1) * page_size

        # 调用CRUD函数获取模特照片
        photos, total, error = crud.model_photo_crud.get_model_photos_by_user(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=page_size,
            is_active=is_active
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        return {
            "success": True,
            "data": {
                "photos": photos,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取模特照片列表错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模特照片列表时发生错误: {str(e)}"
        )


@app.get("/api/model-photos/primary")
async def get_primary_model_photo(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取用户的主要模特照片（用于虚拟试衣）
    参数：
        token: 用户认证令牌
        db: 数据库会话
    返回：
        用户的主要模特照片信息
    """
    try:
        current_user = get_current_user(token, db)

        photo, error = crud.model_photo_crud.get_primary_model_photo(
            db=db,
            user_id=current_user.id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        if not photo:
            return {
                "success": True,
                "message": "用户尚未设置主要模特照片",
                "data": None
            }

        return {
            "success": True,
            "data": photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取主要模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取主要模特照片时发生错误: {str(e)}"
        )


@app.get("/api/model-photos/{photo_id}")
async def get_model_photo_detail(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    获取单张模特照片的详细信息
    参数：
        photo_id: 模特照片ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        模特照片的完整详细信息
    """
    try:
        current_user = get_current_user(token, db)

        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模特照片不存在或无权访问"
            )

        return {
            "success": True,
            "data": photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"获取模特照片详情错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模特照片详情时发生错误: {str(e)}"
        )


@app.put("/api/model-photos/{photo_id}")
async def update_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        photo_name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        is_primary: Optional[bool] = Form(None),
        file: Optional[UploadFile] = File(None)
):
    """
    更新模特照片信息
    参数：
        photo_id: 要更新的模特照片ID
        token: 用户认证令牌
        db: 数据库会话
        photo_name: 新照片名称（可选）
        description: 新描述（可选）
        is_primary: 是否设为主要照片（可选）
        file: 新照片文件（可选）
    返回：
        更新后的模特照片信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片并验证所有权
        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模特照片不存在或无权访问"
            )

        # 更新图片（如果有新图片）
        image_url = photo.image_url
        if file:
            # 删除旧图片
            delete_file(photo.image_url)
            # 保存新图片
            image_url = save_upload_file(file, current_user.id)

            # 更新文件信息
            file_size = file.size
            file_ext = PathLib(file.filename).suffix.lower()
            file_format = file_ext[1:] if file_ext else None

            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary,
                "image_url": image_url,
                "file_size": file_size,
                "file_format": file_format
            }
        else:
            update_data = {
                "photo_name": photo_name,
                "description": description,
                "is_primary": is_primary
            }

        # 清理None值，只传递有值的字段
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # 更新模特照片信息
        updated_photo, error = crud.model_photo_crud.update_model_photo(
            db=db,
            db_photo=photo,
            update_data=update_data
        )

        if error:
            # 如果更新失败且上传了新图片，删除新图片
            if file:
                delete_file(image_url)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "模特照片更新成功",
            "data": updated_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"更新模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新模特照片时发生错误: {str(e)}"
        )


@app.delete("/api/model-photos/{photo_id}")
async def delete_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db),
        hard_delete: bool = Query(False, description="是否永久删除")
):
    """
    删除模特照片（支持软删除和硬删除）
    参数：
        photo_id: 要删除的模特照片ID
        token: 用户认证令牌
        db: 数据库会话
        hard_delete: 是否永久删除（True：硬删除，False：软删除）
    返回：
        删除结果
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片信息（用于可能的文件删除）
        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模特照片不存在或无权访问"
            )

        # 根据参数选择删除方式
        if hard_delete:
            # 永久删除（从数据库完全移除）
            success, error = crud.model_photo_crud.hard_delete_model_photo(
                db=db,
                photo_id=photo_id
            )
        else:
            # 软删除（标记为删除，可恢复）
            success, error = crud.model_photo_crud.delete_model_photo(
                db=db,
                photo_id=photo_id
            )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        # 永久删除时才删除物理文件
        if hard_delete:
            delete_file(photo.image_url)
            if photo.thumbnail_url:
                delete_file(photo.thumbnail_url)

        return {
            "success": True,
            "message": f"模特照片{'永久' if hard_delete else ''}删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"删除模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除模特照片时发生错误: {str(e)}"
        )


@app.post("/api/model-photos/{photo_id}/set-primary")
async def set_primary_model_photo(
        photo_id: int = Path(..., ge=1, description="模特照片ID"),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    设置模特照片为主要照片
    参数：
        photo_id: 要设为主要照片的ID
        token: 用户认证令牌
        db: 数据库会话
    返回：
        更新后的照片信息
    """
    try:
        current_user = get_current_user(token, db)

        # 获取模特照片并验证所有权
        photo, error = crud.model_photo_crud.get_model_photo_by_id(
            db=db,
            user_id=current_user.id,
            photo_id=photo_id
        )

        if error or not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模特照片不存在或无权访问"
            )

        # 更新为主要照片（会自动更新其他照片的is_primary状态）
        updated_photo, error = crud.model_photo_crud.update_model_photo(
            db=db,
            db_photo=photo,
            update_data={"is_primary": True}
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return {
            "success": True,
            "message": "已设置为主要模特照片",
            "data": updated_photo
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"设置主要模特照片错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置主要模特照片时发生错误: {str(e)}"
        )


# ============ 推荐 AI 对话持久化（Your conversations） ============

@app.get("/api/ai/conversations")
async def list_ai_conversations(
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """获取当前用户的推荐 AI 对话列表，按更新时间降序"""
    current_user = get_current_user(token, db)
    items, total, error = crud.ai_conversation_crud.list_by_user(db, user_id=current_user.id)
    if error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    return {
        "success": True,
        "data": [
            {"id": c.id, "title": c.title, "messages": c.messages or [], "created_at": c.created_at.isoformat() if c.created_at else None, "updated_at": c.updated_at.isoformat() if c.updated_at else None}
            for c in items
        ],
        "total": total
    }


@app.get("/api/ai/conversations/{conversation_id}")
async def get_ai_conversation(
        conversation_id: int,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """获取单条对话详情"""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.get_by_id_and_user(db, conversation_id=conversation_id, user_id=current_user.id)
    if error or not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在或无权访问")
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@app.post("/api/ai/conversations")
async def create_ai_conversation(
        body: schemas.AIConversationCreate,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """创建一条新对话"""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.create(db, user_id=current_user.id, title=body.title, messages=body.messages)
    if error or not conv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error or "创建失败")
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@app.put("/api/ai/conversations/{conversation_id}")
async def update_ai_conversation(
        conversation_id: int,
        body: schemas.AIConversationUpdate,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """更新对话标题和/或消息列表"""
    current_user = get_current_user(token, db)
    conv, error = crud.ai_conversation_crud.update(
        db, conversation_id=conversation_id, user_id=current_user.id,
        title=body.title, messages=body.messages
    )
    if error or not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND if not conv else status.HTTP_400_BAD_REQUEST, detail=error or "更新失败")
    return {
        "success": True,
        "data": {"id": conv.id, "title": conv.title, "messages": conv.messages or [], "created_at": conv.created_at.isoformat() if conv.created_at else None, "updated_at": conv.updated_at.isoformat() if conv.updated_at else None}
    }


@app.delete("/api/ai/conversations/{conversation_id}")
async def delete_ai_conversation(
        conversation_id: int,
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """删除一条对话"""
    current_user = get_current_user(token, db)
    ok, error = crud.ai_conversation_crud.delete(db, conversation_id=conversation_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error or "删除失败")
    return {"success": True, "message": "已删除"}


react_agent = ReactAgent()


@app.post("/api/ai/chat/stream")
async def ai_chat_stream(
        req: schemas.ChatReq,
        token: Optional[str] = Query(None, description="用户认证令牌"),
        db: Session = Depends(get_db)
):
    current_user = None
    if token:
        current_user = get_current_user(token, db)

    def event_stream():
        context_token = set_agent_request_user_id(current_user.id if current_user else None)
        try:
            # ReactAgent 当前接口仅接收 query；将历史上下文压成文本前缀传入。
            history_lines = []
            for item in req.history:
                role = item.get("role")
                content = (item.get("content") or "").strip()
                if not content:
                    continue
                if role == "user":
                    history_lines.append(f"用户: {content}")
                elif role == "ai":
                    history_lines.append(f"助手: {content}")

            full_query = req.query
            if history_lines:
                history_text = "\n".join(history_lines[-10:])
                full_query = f"以下是历史对话，请结合上下文回答：\n{history_text}\n\n当前问题：{req.query}"

            previous_text = ""
            for chunk_text in react_agent.execute_stream(full_query):
                if not chunk_text:
                    continue
                if chunk_text.startswith(previous_text):
                    delta = chunk_text[len(previous_text):]
                else:
                    delta = chunk_text
                previous_text = chunk_text
                if not delta:
                    continue
                payload = json.dumps({"type": "delta", "content": delta}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

            yield 'data: {"type":"done"}\n\n'
        except Exception as e:
            error_payload = json.dumps(
                {"type": "error", "message": str(e)}, ensure_ascii=False
            )
            yield f"data: {error_payload}\n\n"
        finally:
            reset_agent_request_user_id(context_token)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============ 错误处理 ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP异常处理
    将FastAPI的HTTP异常转换为统一的JSON响应格式
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    通用异常处理
    捕获所有未处理的异常，返回统一的500错误响应
    """
    error_detail = traceback.format_exc()
    print(f"未处理的异常: {error_detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )


# ============ 应用启动 ============
if __name__ == "__main__":
    import uvicorn

    print("启动服务器: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    # 启动UVicorn服务器，监听所有网络接口，端口8080，开启热重载
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

"""
主应用文件：个人AI衣柜助手API
包含所有业务逻辑和路由定义
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
import traceback

# 导入自定义模块
import models, schemas, crud
from database import engine, get_db

import os
import uuid
from fastapi import UploadFile, File, Form, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import date
import shutil
from pathlib import Path as PathLib

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
# 允许前端跨域请求，开发阶段可以宽松配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",  # HBuilderX默认端口
        "http://localhost:8080",
        "*"  # 开发阶段可以这样，生产环境要指定确切域名
    ],
    allow_credentials=True,  # 允许携带凭证（如cookies）
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# ============ 静态文件服务配置 ============
# 将文件上传目录挂载为静态资源，可通过HTTP直接访问
from fastapi.staticfiles import StaticFiles

app.mount("/Personal-AI-Wardrobe-Assistant/uploads", StaticFiles(directory="/Personal-AI-Wardrobe-Assistant/uploads"), name="uploads")


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
# 上传文件存储目录
UPLOAD_DIR = PathLib("/Personal-AI-Wardrobe-Assistant/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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
        "outfit": "outfit_"
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
    return f"/Personal-AI-Wardrobe-Assistant/uploads/{user_id}/{unique_filename}"


def delete_file(file_url: str) -> bool:
    """
    删除服务器上的文件
    参数：
        file_url: 文件的HTTP URL
    返回：
        是否成功删除
    """
    if file_url.startswith("/uploads/"):
        relative_path = file_url[1:]  # 移除开头的斜杠
        file_path = UPLOAD_DIR.parent / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
    return False


# ============ 服装管理API ============

@app.post("/api/clothing/upload")
async def upload_clothing_item(
        file: UploadFile = File(...),
        name: str = Form(...),
        category: str = Form(...),
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),  # 以逗号分隔的标签字符串
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
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

        # 解析标签字符串为列表
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

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

        # 创建衣物记录
        clothing_item, error = crud.clothing_crud.create_clothing_item(
            db=db,
            user_id=current_user.id,
            item_in=schemas.ClothingItemCreate(
                name=name,
                description=description,
                category=category,
                color=color,
                season=season,
                brand=brand,
                price=price,
                purchase_date=purchase_date_obj,
                tags=tag_list
            ),
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
                "created_at": clothing_item.created_at.isoformat()
            }
        }

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
        is_favorite: Optional[int] = Query(None, description="是否收藏"),
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
            is_favorite=is_favorite,
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
        color: Optional[str] = Form(None),
        season: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        tags: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[float] = Form(None),
        purchase_date: Optional[str] = Form(None),
        is_favorite: Optional[int] = Form(None),
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
        category: 新分类（可选）
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
            category=category,
            color=color,
            season=season,
            brand=brand,
            price=price,
            purchase_date=purchase_date_obj,
            is_favorite=is_favorite,
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
        db: Session = Depends(get_db),
        target_level: Optional[int] = Query(None, ge=0, le=3, description="指定目标等级，不传则循环")
):
    """
    切换衣物的收藏等级
    参数：
        clothing_id: 衣物ID
        token: 用户认证令牌
        db: 数据库会话
        target_level: 指定目标等级（0-3），不传则循环递增
    返回：
        更新后的收藏等级
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

        # 确定下一个等级
        if target_level is not None:
            next_favorite = target_level
        else:
            # 循环递增：0->1->2->3->0
            next_favorite = (item.is_favorite + 1) % 4

        update_data = schemas.ClothingItemUpdate(is_favorite=next_favorite)

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

        favorite_labels = {
            0: "不喜欢",
            1: "一般",
            2: "喜欢",
            3: "非常喜欢"
        }

        return {
            "success": True,
            "message": f"收藏等级已{'设置' if target_level is not None else '切换'}为：{favorite_labels[updated_item.is_favorite]}",
            "data": {
                "is_favorite": updated_item.is_favorite,
                "favorite_label": favorite_labels[updated_item.is_favorite]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"切换收藏等级错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换收藏等级时发生错误: {str(e)}"
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
        is_primary: Optional[bool] = Form(False),
        token: str = Query(...),
        db: Session = Depends(get_db)
):
    """
    上传模特照片（用于虚拟试衣功能）
    参数：
        file: 模特照片文件
        photo_name: 照片名称
        description: 照片描述（可选）
        is_primary: 是否设为主要照片（可选，默认False）
        token: 用户认证令牌
        db: 数据库会话
    返回：
        上传成功的模特照片信息
    """
    try:
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
            is_primary=is_primary
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


# ============ 错误处理 ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    HTTP异常处理
    将FastAPI的HTTP异常转换为统一的JSON响应格式
    """
    return {
        "success": False,
        "message": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    通用异常处理
    捕获所有未处理的异常，返回统一的500错误响应
    """
    error_detail = traceback.format_exc()
    print(f"未处理的异常: {error_detail}")
    return {
        "success": False,
        "message": "服务器内部错误",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
    }


# ============ 应用启动 ============
if __name__ == "__main__":
    import uvicorn

    print("启动服务器: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    # 启动UVicorn服务器，监听所有网络接口，端口8000，开启热重载
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
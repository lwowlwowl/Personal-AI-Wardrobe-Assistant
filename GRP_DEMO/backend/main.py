import sys
import os
import traceback
import io
import json
import requests
import logging
import hashlib
import time
from datetime import datetime, timedelta
from fastapi.exceptions import RequestValidationError
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. 针对 Windows 环境的c编码修复环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"

from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入自定义模块
import models, schemas, crud
from database import engine, get_db

# 导入虚拟试穿模块
try:
    from comfyui_client import comfyui_client, build_virtual_tryon_workflow
    
    # 🔥 暴力修正：不管配置文件怎么写，强制让对象指向 8118
    comfyui_client.server_address = "http://127.0.0.1:8118"
    print(f"🚀 [重要] 已强制将 ComfyUI 地址指向: {comfyui_client.server_address}")

    COMFYUI_AVAILABLE = True
except ImportError as e:
    COMFYUI_AVAILABLE = False
    logger.warning(f"警告: ComfyUI客户端模块加载失败 ({e})，虚拟试穿功能将不可用")

# 导入衣柜管理模块
try:
    from wardrobe_crud import (
        add_clothing_item, get_clothing_items, update_clothing_item,
        delete_clothing_item, analyze_wardrobe, get_recommendations
    )

    WARDROBE_AVAILABLE = True
except ImportError:
    WARDROBE_AVAILABLE = False
    logger.warning("警告: 衣柜管理模块未找到，衣柜功能将不可用")

# 导入AI推荐模块
try:
    from llm_recommendation import get_llm_recommendation

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("警告: LLM推荐模块未找到，AI推荐功能将不可用")

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# ============ FastAPI应用配置 ============
# 1. 确保在文件最上面（import 区域）有这行导入：
from fastapi.middleware.cors import CORSMiddleware

# 2. 这是你刚才找到的 app 定义
app = FastAPI(
    title="Personal AI Wardrobe Assistant API",
    description="个人AI衣柜助手后端API - 包含虚拟试穿、衣柜管理、AI推荐等功能",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ 参数验证失败: {exc.errors()}") # 这行会在黑窗口打印到底是哪个参数错了
    return JSONResponse(
        status_code=422,
        content={"success": False, "detail": exc.errors()}
    )

# 3. 👇 把下面这段直接复制粘贴到 app 定义的紧下方 👇
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有的前端域名访问（本地开发用 "*" 最稳妥）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有的请求方法（GET, POST, OPTIONS 等）
    allow_headers=["*"],  # 允许所有的请求头（非常关键！这样才能允许前端传自定义的 'token'）
)

# ============ CORS配置 ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# ============ 自定义异常处理器 ============
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )


@app.exception_handler(Exception)
async def custom_universal_exception_handler(request: Request, exc: Exception):
    error_detail = traceback.format_exc()
    logger.error(f"未处理的异常: {error_detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "服务器内部错误"}
    )


# ============ 健康检查与系统信息 ============
@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Personal AI Wardrobe Assistant API v2.0",
        "endpoints": ["auth", "users", "wardrobe", "virtual_tryon", "recommendation"]
    }


@app.get("/api/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "services": {
            "comfyui": COMFYUI_AVAILABLE,
            "wardrobe": WARDROBE_AVAILABLE,
            "llm": LLM_AVAILABLE
        }
    }
    if COMFYUI_AVAILABLE:
        try:
            response = requests.get(f"{comfyui_client.server_address}/system_stats", timeout=3)
            health_status["services"]["comfyui_connected"] = response.status_code == 200
        except:
            health_status["services"]["comfyui_connected"] = False
    return health_status


# ============ 用户认证相关接口 ============
@app.post("/api/auth/register")
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    user_data = user.dict(exclude={'confirm_password'})
    db_user, error = crud.create_user(db, user_data)

    if error:
        raise HTTPException(status_code=409 if "已注册" in error else 400, detail=error)

    return {"success": True, "message": "注册成功", "data": {"id": db_user.id, "username": db_user.username}}


@app.post("/api/auth/login")
async def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user, error = crud.authenticate_user(db, login_data.username, login_data.password)
    if error:
        raise HTTPException(status_code=401, detail=error)

    expires = timedelta(days=7) if login_data.remember else timedelta(minutes=120)
    access_token = crud.create_access_token(data={"sub": user.username, "user_id": user.id}, expires_delta=expires)

    return {
        "success": True,
        "access_token": access_token,
        "user": {"id": user.id, "username": user.username}
    }


@app.get("/api/auth/verify")
async def verify_token(token: str, db: Session = Depends(get_db)):
    payload = crud.verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的token")

    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="账号状态异常")

    return {"valid": True, "user": {"id": user.id, "username": user.username}}


# ============ 虚拟试穿接口 (核心修改) ============
if COMFYUI_AVAILABLE:
    @app.post("/api/virtual-try-on/generate")
    async def generate_virtual_tryon(
    person_image: str = Form("2.jpg"),        # 给它个默认值
    clothing_image: str = Form("2.jpg"),      # 给它个默认值
    token: Optional[str] = Form(None),         # 👈 把 (...) 改成 None，这是解决 422 的关键！
    accessory_image: Optional[str] = Form(None),
    model_type: str = Form("2509"),
    prompt: str = Form("")
):
    # 进去之后的第一件事：强行打印，证明我们进来了
        print("🚀 [突破成功] 后端已经接收到请求，开始对接 ComfyUI...")
        """基于 Qwen2.5-VL 的图像编辑/试穿接口"""
        # 1. 验证身份
        #payload = crud.verify_access_token(token)
        #if not payload:
            #raise HTTPException(status_code=401, detail="认证失败")

        try:
            # 2. 构建 Qwen 工作流
            workflow = build_virtual_tryon_workflow(
                person_image=person_image,
                clothing_image=clothing_image,
                #accessory_image=accessory_image,
                model_type=model_type,
                prompt_text=prompt
            )

            # 3. 提交任务
            prompt_id = comfyui_client.queue_prompt(workflow)
            if not prompt_id:
                raise HTTPException(status_code=500, detail="ComfyUI 队列满或连接失败")

            # 4. 轮询等待
            result = comfyui_client.wait_for_completion(prompt_id)

            # 5. 提取并返回图片 (SaveImage 节点 ID 60)
            output_images = result.get("outputs", {})
            if "60" in output_images:
                images = output_images["60"].get("images", [])
                if images:
                    img_info = images[0]
                    img_bytes = comfyui_client.get_image(
                        filename=img_info["filename"],
                        subfolder=img_info.get("subfolder", ""),
                        folder_type=img_info.get("type", "output")
                    )
                    return StreamingResponse(
                        io.BytesIO(img_bytes),
                        media_type="image/png",
                        headers={"X-Prompt-ID": prompt_id}
                    )

            raise HTTPException(status_code=500, detail="未能生成图片结果")

        except Exception as e:
            logger.error(f"虚拟试穿失败: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/virtual-try-on/upload-image")
async def upload_virtual_tryon_image(file: UploadFile = File(...), token: str = Form(...)):
    # 👇 注意：下面所有的行，左边都要比 async def 多出 4 个空格
    print(f"DEBUG: 接收到请求，准备校验 Token...")

    # 2. 校验 Token
    payload = crud.verify_access_token(token)
    if not payload:
        print("❌ Token 验证失败！")
        raise HTTPException(status_code=401, detail="未授权：Token 失效")

    # 3. 读取并尝试上传到 ComfyUI
    try:
        content = await file.read()
        # 🚨 核心排查点：确保你的 ComfyUI 软件已经打开！
        res = comfyui_client.upload_image(content, filename=file.filename)
        
        if not res:
            print("❌ ComfyUI 拒绝了图片上传，请检查 ComfyUI 是否已启动在 8118 端口")
            raise HTTPException(status_code=500, detail="ComfyUI 服务器未响应，请检查后台软件是否运行")
            
        print(f"✅ 图片上传成功: {res.get('name')}")
        return {"success": True, "filename": res.get("name")}
        
    except Exception as e:
        print(f"❌ 后端内部错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"渲染引擎连接异常: {str(e)}")

# ============ 衣柜与通用接口 (简化) ============
@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...), token: str = Form(...)):
    if not crud.verify_access_token(token):
        raise HTTPException(status_code=401, detail="未授权")

    file_data = await file.read()
    file_hash = hashlib.md5(file_data).hexdigest()[:8]
    filename = f"upload_{int(time.time())}_{file_hash}.png"
    # 这里视具体需求保存到本地路径或 OSS
    return {"success": True, "filename": filename}


@app.get("/api/weather/now")
async def weather_now():
    return {"temp": "22°C", "text": "晴朗", "suggestion": "适合穿轻便的春装"}


# ============ 应用启动 ============
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
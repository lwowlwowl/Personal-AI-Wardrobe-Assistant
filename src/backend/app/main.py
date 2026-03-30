"""
FastAPI application: middleware, static files, routers, exception handlers.
Bootstrap paths stay here so they run before ORM metadata is used.
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path as PathLib

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import app.models as models
from app.api.router import api_router
from app.core.database import engine
from app.core.exceptions import AppError
from app.services.file_service import UPLOAD_DIR, UPLOAD_URL_PREFIX

# backend/ (this file: backend/app/main.py)
BACKEND_DIR = PathLib(__file__).resolve().parent.parent
AIWARDROBE_DIR = BACKEND_DIR / "AIwardrobe"
if str(AIWARDROBE_DIR) not in sys.path:
    sys.path.insert(0, str(AIWARDROBE_DIR))

# .env is loaded on first import via app.core.config (same timing as database/engine)

try:
    from app.services.comfyui_client import build_virtual_tryon_workflow, comfyui_client

    _comfy_addr = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8118").rstrip("/")
    comfyui_client.server_address = _comfy_addr
    COMFYUI_AVAILABLE = True
    print(f"ComfyUI virtual try-on enabled, server: {comfyui_client.server_address}")
except ImportError as _e:
    comfyui_client = None  # type: ignore
    build_virtual_tryon_workflow = None  # type: ignore
    COMFYUI_AVAILABLE = False
    print(f"ComfyUI virtual try-on disabled (missing deps or app.services.comfyui_client): {_e}")

from app import runtime as app_runtime

app_runtime.COMFYUI_AVAILABLE = COMFYUI_AVAILABLE
app_runtime.comfyui_client = comfyui_client
app_runtime.build_virtual_tryon_workflow = build_virtual_tryon_workflow

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal AI Wardrobe Assistant API",
    description="Backend API for Personal AI Wardrobe Assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:9000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(UPLOAD_URL_PREFIX, StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )

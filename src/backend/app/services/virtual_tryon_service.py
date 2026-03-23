"""
虚拟试穿业务编排；路由层仅处理 UploadFile 读取与 JSONResponse 包装。
响应形状与状态码与重构前 virtual_tryon 路由一致。
"""
from __future__ import annotations

import base64
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import app.crud as crud
import app.schemas as schemas
from app import runtime as app_runtime
from app.services.file_service import UPLOAD_DIR, UPLOAD_URL_PREFIX
from fastapi import HTTPException
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class JsonEnvelope:
    """需以 JSONResponse(status_code, content=body) 返回（与原路由一致）。"""

    status_code: int
    body: Dict[str, Any]


def clean_token(raw: Optional[str]) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().strip('"').strip("'")
    return s


def _resolve_storage_path_from_image_ref(image_ref: str) -> Optional[Path]:
    """将前端传入的衣柜静态 URL 解析为本机 uploads 内安全路径。"""
    s = (image_ref or "").strip()
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        s = urlparse(s).path or ""
    if not s.startswith(UPLOAD_URL_PREFIX + "/"):
        return None
    rel = s[len(UPLOAD_URL_PREFIX) + 1 :].lstrip("/")
    if not rel or ".." in rel.replace("\\", "/"):
        return None
    base = UPLOAD_DIR.resolve()
    candidate = (UPLOAD_DIR / rel).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def run_upload_virtual_tryon_from_storage(
    body: schemas.VirtualTryOnUploadFromStorageRequest,
    db: Session,
) -> Union[dict, JsonEnvelope]:
    """
    從本機 uploads 讀取圖片並上傳到 ComfyUI，避免前端 uni.downloadFile 失敗（小程序域名等）。
    """
    if not app_runtime.COMFYUI_AVAILABLE or not app_runtime.comfyui_client:
        return JsonEnvelope(
            status_code=503,
            body={
                "success": False,
                "message": "虚拟试穿未启用：请确认 app/services/comfyui_client.py 可用，且 app/resources/qwen_edit_v1.json 存在",
            },
        )

    t = clean_token(body.token)
    payload = crud.verify_access_token(t) if t else None
    if not payload:
        raise HTTPException(status_code=401, detail="未授权：Token 失效")

    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="账号状态异常")

    path = _resolve_storage_path_from_image_ref(body.image_ref)
    if path is None:
        raise HTTPException(
            status_code=400,
            detail="无效的图片路径：请使用衣柜/模特图的有效地址（Personal-AI-Wardrobe-Assistant/uploads/...）",
        )

    rel_under_upload = path.relative_to(UPLOAD_DIR.resolve())
    parts = str(rel_under_upload).replace("\\", "/").split("/")
    if parts and str(user.id) != parts[0]:
        raise HTTPException(status_code=403, detail="无权访问该图片文件")

    try:
        file_content = path.read_bytes()
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"读取图片失败: {e}") from e

    cc = app_runtime.comfyui_client
    try:
        res = cc.upload_image(file_content, filename=path.name)
        if not res:
            raise HTTPException(
                status_code=503,
                detail="ComfyUI 未响应，请确认 ComfyUI 已启动且地址正确（可用环境变量 COMFYUI_SERVER 配置）",
            )
        name = res.get("name")
        return {"success": True, "filename": name, "data": {"filename": name}}
    except HTTPException:
        raise
    except Exception as e:
        print(f"virtual_tryon upload-from-storage error:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}") from e


async def run_upload_virtual_tryon_image(
    *,
    file_content: bytes,
    filename: Optional[str],
    token: str,
    image_type: Optional[str],
    db: Session,
) -> Union[dict, JsonEnvelope]:
    _ = image_type
    if not app_runtime.COMFYUI_AVAILABLE or not app_runtime.comfyui_client:
        return JsonEnvelope(
            status_code=503,
            body={
                "success": False,
                "message": "虚拟试穿未启用：请确认 app/services/comfyui_client.py 可用，且 app/resources/qwen_edit_v1.json 存在",
            },
        )

    t = clean_token(token)
    payload = crud.verify_access_token(t) if t else None
    if not payload:
        raise HTTPException(status_code=401, detail="未授权：Token 失效")

    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="账号状态异常")

    cc = app_runtime.comfyui_client
    try:
        res = cc.upload_image(file_content, filename=filename)
        if not res:
            raise HTTPException(
                status_code=503,
                detail="ComfyUI 未响应，请确认 ComfyUI 已启动且地址正确（可用环境变量 COMFYUI_SERVER 配置）",
            )
        name = res.get("name")
        return {"success": True, "filename": name, "data": {"filename": name}}
    except HTTPException:
        raise
    except Exception as e:
        print(f"virtual_tryon upload-image error:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}") from e


def run_generate_virtual_tryon(
    body: schemas.VirtualTryOnGenerateRequest,
    db: Session,
) -> Union[dict, JsonEnvelope]:
    if (
        not app_runtime.COMFYUI_AVAILABLE
        or not app_runtime.comfyui_client
        or not app_runtime.build_virtual_tryon_workflow
    ):
        return JsonEnvelope(
            status_code=503,
            body={"success": False, "message": "虚拟试穿未启用"},
        )

    t = clean_token(body.token)
    if not t:
        return JsonEnvelope(200, {"success": False, "message": "请先登录"})
    payload = crud.verify_access_token(t)
    if not payload:
        return JsonEnvelope(200, {"success": False, "message": "未授权：Token 失效"})
    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        return JsonEnvelope(200, {"success": False, "message": "账号状态异常"})

    cc = app_runtime.comfyui_client
    bwf = app_runtime.build_virtual_tryon_workflow

    try:
        workflow = bwf(
            person_image=body.person_image,
            clothing_image=body.clothing_image,
            accessory_image=None,
            model_type=body.model_type or "2509",
            prompt_text=body.prompt or "",
        )
        prompt_id = cc.queue_prompt(workflow)
        if not prompt_id:
            return JsonEnvelope(
                200,
                {"success": False, "message": "ComfyUI 队列满或连接失败"},
            )

        result = cc.wait_for_completion(prompt_id)
        output_images = (result or {}).get("outputs", {})
        if "60" not in output_images:
            return JsonEnvelope(
                200,
                {
                    "success": False,
                    "message": "未能生成图片结果（工作流输出节点 60 无数据）",
                },
            )

        images = output_images["60"].get("images", [])
        if not images:
            return JsonEnvelope(
                200,
                {"success": False, "message": "未能生成图片结果"},
            )

        img_info = images[0]
        img_bytes = cc.get_image(
            filename=img_info["filename"],
            subfolder=img_info.get("subfolder", ""),
            folder_type=img_info.get("type", "output"),
        )
        if not img_bytes:
            print(
                "❌ [virtual_tryon] img_bytes empty — ComfyUI may not have finished writing the file yet"
            )
            return JsonEnvelope(
                200,
                {"success": False, "message": "无法读取生成图片"},
            )

        fn = img_info.get("filename", "")
        print(f"✅ [virtual_tryon] image ok — filename={fn}, size={len(img_bytes)} bytes")
        try:
            debug_path = Path(__file__).resolve().parent.parent.parent / "debug_result.png"
            debug_path.write_bytes(img_bytes)
        except OSError as werr:
            print(f"virtual_tryon: could not write debug_result.png: {werr}")

        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        return {
            "success": True,
            "data": {
                "result_image": data_url,
                "image_size_bytes": len(img_bytes),
            },
        }
    except HTTPException as he:
        return JsonEnvelope(200, {"success": False, "message": str(he.detail)})
    except Exception as e:
        print(f"virtual_tryon generate error:\n{traceback.format_exc()}")
        return JsonEnvelope(
            200,
            {"success": False, "message": f"生成失败: {str(e)}"},
        )

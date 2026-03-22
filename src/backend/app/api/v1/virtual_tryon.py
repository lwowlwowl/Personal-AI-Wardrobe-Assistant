import base64
import traceback
from typing import Optional

import app.crud as crud
import app.schemas as schemas
from app import runtime as app_runtime
from app.core.database import get_db
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

router = APIRouter(tags=["virtual-try-on"])


def _clean_token(raw: Optional[str]) -> str:
    if raw is None:
        return ""
    s = str(raw).strip().strip('"').strip("'")
    return s


@router.post("/api/virtual-try-on/upload-image")
async def upload_virtual_tryon_image(
    file: UploadFile = File(...),
    token: str = Form(...),
    image_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if not app_runtime.COMFYUI_AVAILABLE or not app_runtime.comfyui_client:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "虚拟试穿未启用：请确认 app/services/comfyui_client.py 可用，且 app/resources/qwen_edit_v1.json 存在",
            },
        )

    _ = image_type
    t = _clean_token(token)
    payload = crud.verify_access_token(t) if t else None
    if not payload:
        raise HTTPException(status_code=401, detail="未授权：Token 失效")

    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="账号状态异常")

    cc = app_runtime.comfyui_client
    try:
        content = await file.read()
        res = cc.upload_image(content, filename=file.filename)
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
        print(f"[virtual-try-on] upload-image 错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/api/virtual-try-on/generate")
async def generate_virtual_tryon(
    body: schemas.VirtualTryOnGenerateRequest,
    db: Session = Depends(get_db),
):
    if (
        not app_runtime.COMFYUI_AVAILABLE
        or not app_runtime.comfyui_client
        or not app_runtime.build_virtual_tryon_workflow
    ):
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "虚拟试穿未启用"},
        )

    t = _clean_token(body.token)
    if not t:
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": "请先登录"},
        )
    payload = crud.verify_access_token(t)
    if not payload:
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": "未授权：Token 失效"},
        )
    user = crud.get_user_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": "账号状态异常"},
        )

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
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "ComfyUI 队列满或连接失败"},
            )

        result = cc.wait_for_completion(prompt_id)
        output_images = (result or {}).get("outputs", {})
        if "60" not in output_images:
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "未能生成图片结果（工作流输出节点 60 无数据）"},
            )

        images = output_images["60"].get("images", [])
        if not images:
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "未能生成图片结果"},
            )

        img_info = images[0]
        img_bytes = cc.get_image(
            filename=img_info["filename"],
            subfolder=img_info.get("subfolder", ""),
            folder_type=img_info.get("type", "output"),
        )
        if not img_bytes:
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "无法读取生成图片"},
            )

        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        return {
            "success": True,
            "data": {"result_image": data_url},
        }
    except HTTPException as he:
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": str(he.detail)},
        )
    except Exception as e:
        print(f"[virtual-try-on] generate 错误: {traceback.format_exc()}")
        return JSONResponse(
            status_code=200,
            content={"success": False, "message": f"生成失败: {str(e)}"},
        )

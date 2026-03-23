from app.core.database import get_db
from app.services.virtual_tryon_service import (
    JsonEnvelope,
    PngBytesResult,
    run_generate_virtual_tryon,
    run_upload_virtual_tryon_from_storage,
    run_upload_virtual_tryon_image,
)
import app.schemas as schemas
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

router = APIRouter(tags=["virtual-try-on"])


@router.post("/api/virtual-try-on/upload-image")
async def upload_virtual_tryon_image(
    file: UploadFile = File(...),
    token: str = Form(...),
    image_type: str | None = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    out = await run_upload_virtual_tryon_image(
        file_content=content,
        filename=file.filename,
        token=token,
        image_type=image_type,
        db=db,
    )
    if isinstance(out, JsonEnvelope):
        return JSONResponse(status_code=out.status_code, content=out.body)
    return out


@router.post("/api/virtual-try-on/upload-from-storage")
async def upload_virtual_tryon_from_storage(
    body: schemas.VirtualTryOnUploadFromStorageRequest,
    db: Session = Depends(get_db),
):
    """由本机 uploads 路径直接转 ComfyUI，避免前端 downloadFile 跨域/白名单问题。"""
    out = run_upload_virtual_tryon_from_storage(body, db)
    if isinstance(out, JsonEnvelope):
        return JSONResponse(status_code=out.status_code, content=out.body)
    return out


@router.post("/api/virtual-try-on/generate")
async def generate_virtual_tryon(
    body: schemas.VirtualTryOnGenerateRequest,
    db: Session = Depends(get_db),
):
    out = run_generate_virtual_tryon(body, db)
    if isinstance(out, JsonEnvelope):
        return JSONResponse(status_code=out.status_code, content=out.body)
    if isinstance(out, PngBytesResult):
        nbytes = len(out.data)
        return Response(
            content=out.data,
            media_type="image/png",
            headers={
                "X-Result-Image-Bytes": str(nbytes),
                "Content-Length": str(nbytes),
            },
        )
    return out

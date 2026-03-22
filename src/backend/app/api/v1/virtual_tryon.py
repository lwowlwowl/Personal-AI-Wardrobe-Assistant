from app.core.database import get_db
from app.services.virtual_tryon_service import JsonEnvelope, run_generate_virtual_tryon, run_upload_virtual_tryon_image
import app.schemas as schemas
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
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


@router.post("/api/virtual-try-on/generate")
async def generate_virtual_tryon(
    body: schemas.VirtualTryOnGenerateRequest,
    db: Session = Depends(get_db),
):
    out = run_generate_virtual_tryon(body, db)
    if isinstance(out, JsonEnvelope):
        return JSONResponse(status_code=out.status_code, content=out.body)
    if isinstance(out, dict) and out.get("success") and isinstance(out.get("data"), dict):
        nbytes = out["data"].get("image_size_bytes")
        if isinstance(nbytes, int):
            return JSONResponse(
                content=out,
                headers={"X-Result-Image-Bytes": str(nbytes)},
            )
    return out

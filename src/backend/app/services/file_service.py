"""上傳目錄與檔案儲存（與原 main.py 邏輯一致）。"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

# backend/app/services/file_service.py → parents[4] = 專案根（與 main.py 中 BASE_DIR 一致）
_REPO_ROOT = Path(__file__).resolve().parents[4]

UPLOAD_URL_PREFIX = "/Personal-AI-Wardrobe-Assistant/uploads"
UPLOAD_DIR = _REPO_ROOT / "uploads"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_upload_file(file: UploadFile, user_id: int, file_type: str = "clothing") -> str:
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型，请上传 {', '.join(ALLOWED_EXTENSIONS)} 格式的图片",
        )

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小不能超过 {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    prefix_map = {
        "clothing": "clothing_",
        "model": "model_",
        "outfit": "outfit_",
        "avatar": "avatar_",
    }
    prefix = prefix_map.get(file_type, "")
    unique_filename = f"{prefix}{uuid.uuid4().hex}{file_ext}"
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(exist_ok=True)

    file_path = user_dir / unique_filename
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return f"{UPLOAD_URL_PREFIX}/{user_id}/{unique_filename}"


def delete_file(file_url: str) -> bool:
    if file_url.startswith(f"{UPLOAD_URL_PREFIX}/"):
        relative_path = file_url[len(UPLOAD_URL_PREFIX) + 1 :]
        file_path = UPLOAD_DIR / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
    return False

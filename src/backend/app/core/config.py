"""
集中載入環境變數與應用設定。
與修改.md Phase 3 對齊；路徑載入順序與原 main.py / database.py 行為相容。
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# backend/ 目錄（本檔位於 backend/app/core/config.py）
_BACKEND_DIR = Path(__file__).resolve().parents[2]

load_dotenv(_BACKEND_DIR / ".env", override=False)
_ai_env = _BACKEND_DIR / "AIwardrobe" / "config" / ".env"
if _ai_env.exists():
    load_dotenv(_ai_env, override=False)
load_dotenv(override=False)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/wardrobe_db",
)

SQL_ECHO = os.getenv("SQL_ECHO", "False").lower() == "true"

# 未設定 SECRET_KEY 時與舊 crud 行為一致：每次行程啟動隨機（開發用；生產請設環境變數）
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
RESET_TOKEN_EXPIRE_MINUTES = 30

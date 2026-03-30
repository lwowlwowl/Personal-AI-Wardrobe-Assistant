"""
Load environment variables and application settings.
Load order matches legacy main.py / database.py behavior.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# backend/ root (this file: backend/app/core/config.py)
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

# If SECRET_KEY is unset, match legacy behavior: random per process (dev only; set in prod)
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
RESET_TOKEN_EXPIRE_MINUTES = 30

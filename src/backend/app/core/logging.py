"""應用日誌：統一取得 Logger（與修改.md 對齊）。"""
import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name if name else "app")

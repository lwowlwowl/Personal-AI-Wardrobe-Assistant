"""統一 JSON 結構輔助（與修改.md 對齊；逐步採用即可）。"""
from __future__ import annotations

from typing import Any, Dict, Optional


def success_body(
    *,
    data: Any = None,
    message: str = "ok",
    status_code: int = 200,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "success": True,
        "message": message,
        "status_code": status_code,
    }
    if data is not None:
        out["data"] = data
    if extra:
        out.update(extra)
    return out


def error_body(message: str, status_code: int = 400) -> Dict[str, Any]:
    return {"success": False, "message": message, "status_code": status_code}

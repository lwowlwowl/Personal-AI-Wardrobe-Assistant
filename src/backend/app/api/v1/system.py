from typing import Any, Dict

from fastapi import APIRouter

from app import runtime as app_runtime

router = APIRouter(tags=["system"])


@router.get("/")
async def root():
    """Root path: basic API info."""
    return {
        "message": "Personal AI Wardrobe Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@router.get("/api/health")
async def health_check():
    """Health check for monitoring."""
    out: Dict[str, Any] = {"status": "healthy", "message": "API is running"}
    if app_runtime.COMFYUI_AVAILABLE and app_runtime.comfyui_client:
        cc = app_runtime.comfyui_client
        out["virtual_tryon"] = {
            "enabled": True,
            "comfyui_server": cc.server_address,
        }
        try:
            import requests as _req

            _r = _req.get(f"{cc.server_address}/system_stats", timeout=3)
            out["virtual_tryon"]["comfyui_reachable"] = _r.status_code == 200
        except Exception:
            out["virtual_tryon"]["comfyui_reachable"] = False
    else:
        out["virtual_tryon"] = {"enabled": False}
    return out

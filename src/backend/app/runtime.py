"""由 main 在啟動時賦值的行程級狀態，供路由子模組讀取，避免循環 import main。"""
from typing import Any, Callable, Optional

COMFYUI_AVAILABLE: bool = False
comfyui_client: Optional[Any] = None
build_virtual_tryon_workflow: Optional[Callable[..., Any]] = None

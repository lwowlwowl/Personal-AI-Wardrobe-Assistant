"""Process-wide state set by main at startup; read by routes to avoid circular imports of main."""
from typing import Any, Callable, Optional

COMFYUI_AVAILABLE: bool = False
comfyui_client: Optional[Any] = None
build_virtual_tryon_workflow: Optional[Callable[..., Any]] = None

"""
ComfyUI HTTP client and virtual try-on workflow builder (resource: app/resources/qwen_edit_v1.json).
"""
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

# app/services/ -> app/resources/
_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


class ComfyUIClient:
    def __init__(self, server_address: str = "http://127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        # Session that ignores env proxy settings (trust_env=False) to avoid broken system proxies.
        self.session = requests.Session()
        self.session.trust_env = False

    def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        try:
            payload = {"prompt": prompt, "client_id": self.client_id}
            response = self.session.post(
                f"{self.server_address}/prompt",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("prompt_id")
            return None
        except Exception as e:
            print(f"ComfyUI queue_prompt failed: {e}")
            raise HTTPException(status_code=503, detail="Failed to connect to ComfyUI service")

    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(f"{self.server_address}/history/{prompt_id}")
            return response.json().get(prompt_id) if response.status_code == 200 else None
        except Exception:
            return None

    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            response = self.session.get(f"{self.server_address}/view", params=params)
            return response.content if response.status_code == 200 else None
        except Exception:
            return None

    def upload_image(self, image_data: bytes, filename: str = None, type: str = "input") -> Optional[Dict[str, str]]:
        try:
            if not filename:
                filename = f"upload_{int(time.time())}.png"
            files = {"image": (filename, image_data)}
            data = {"type": type}
            response = self.session.post(f"{self.server_address}/upload/image", files=files, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"ComfyUI upload_image failed, status={response.status_code}")
                return None
        except Exception as e:
            print(f"ComfyUI upload_image error: {e}")
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 600) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            if history and history.get("status", {}).get("completed"):
                return history
            time.sleep(2)
        raise HTTPException(status_code=408, detail="Task execution timed out")


def build_virtual_tryon_workflow(
        person_image: str,
        clothing_image: str,
        accessory_image: Optional[str] = None,
        model_type: str = "2509",
        prompt_text: str = ""
) -> Dict[str, Any]:
    """Build a ComfyUI prompt dict from the Qwen-Image-Edit workflow template."""
    template_path = _RESOURCES_DIR / "qwen_edit_v1.json"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"ComfyUI workflow template load failed: {e}")
        raise HTTPException(status_code=500, detail="Workflow template is missing")

    # --- Map image inputs ---
    # 78: person image (Image 1)
    if "78" in workflow:
        workflow["78"]["inputs"]["image"] = person_image

    # 106: clothing image (Image 2)
    if "106" in workflow:
        workflow["106"]["inputs"]["image"] = clothing_image

    # 108: accessory image (Image 3)
    # If no accessory image, leave workflow default to avoid invalid node state.
    if "108" in workflow and accessory_image:
        workflow["108"]["inputs"]["image"] = accessory_image

    # --- Map prompts ---
    # 111: positive prompt encoding
    if "111" in workflow:
        default_prompt = (
            "Put the clothing from image 2 onto the person in image 1, "
            "add earrings from image 3 in a subtle size, and preserve all other person features from image 1."
        )
        workflow["111"]["inputs"]["prompt"] = prompt_text if prompt_text else default_prompt

    # 110: negative prompt (mirror image refs for Qwen context)
    if "110" in workflow:
        workflow["110"]["inputs"]["image1"] = workflow["111"]["inputs"]["image1"]
        workflow["110"]["inputs"]["image2"] = workflow["111"]["inputs"]["image2"]

    # --- Map model weights ---
    # model_type "2509" selects safetensors names from the bundled JSON
    if model_type == "2509":
        if "37" in workflow:
            workflow["37"]["inputs"]["unet_name"] = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
        if "89" in workflow:
            workflow["89"]["inputs"]["lora_name"] = "Qwen-Image-Edit-Lightning-4steps-V1.0.safetensors"

    # Output filename prefix
    if "60" in workflow:
        workflow["60"]["inputs"]["filename_prefix"] = f"QwenEdit_{int(time.time())}"

    return workflow


comfyui_client = ComfyUIClient(server_address="http://127.0.0.1:8188")

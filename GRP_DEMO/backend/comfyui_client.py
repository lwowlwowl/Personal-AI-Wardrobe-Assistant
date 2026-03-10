import json
import requests
import time
import uuid
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class ComfyUIClient:
    def __init__(self, server_address: str = "http://127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        # ✨ 核心修正：创建一个不信任环境变量（绕过系统代理）的 Session
        self.session = requests.Session()
        self.session.trust_env = False

    def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        try:
            payload = {"prompt": prompt, "client_id": self.client_id}
            # ⬇️ 这里改用 self.session.post
            response = self.session.post(
                f"{self.server_address}/prompt",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10 # 增加超时保护
            )
            if response.status_code == 200:
                return response.json().get("prompt_id")
            return None
        except Exception as e:
            logger.error(f"提交任务失败: {str(e)}")
            raise HTTPException(status_code=503, detail="ComfyUI服务连接失败")

    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        try:
            # ⬇️ 这里改用 self.session.get
            response = self.session.get(f"{self.server_address}/history/{prompt_id}")
            return response.json().get(prompt_id) if response.status_code == 200 else None
        except Exception:
            return None

    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> Optional[bytes]:
        try:
            params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            # ⬇️ 这里改用 self.session.get
            response = self.session.get(f"{self.server_address}/view", params=params)
            return response.content if response.status_code == 200 else None
        except Exception:
            return None

    def upload_image(self, image_data: bytes, filename: str = None, type: str = "input") -> Optional[Dict[str, str]]:
        try:
            if not filename: filename = f"upload_{int(time.time())}.png"
            files = {"image": (filename, image_data)}
            data = {"type": type}
            # ⬇️ 这里改用 self.session.post
            response = self.session.post(f"{self.server_address}/upload/image", files=files, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"上传图片失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"上传图片异常: {str(e)}")
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 600) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            if history and history.get("status", {}).get("completed"):
                return history
            time.sleep(2)
        raise HTTPException(status_code=408, detail="任务执行超时")


def build_virtual_tryon_workflow(
        person_image: str,
        clothing_image: str,
        accessory_image: Optional[str] = None,
        model_type: str = "2509",
        prompt_text: str = ""
) -> Dict[str, Any]:
    """
    根据 Qwen-Image-Edit 工作流构建任务
    """
    # 加载你提供的 JSON 模板 (建议保存为 qwen_edit_v1.json)
    template_path = os.path.join(os.path.dirname(__file__), "qwen_edit_v1.json")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        logger.error(f"加载模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail="工作流模板丢失")

    # --- 映射图片输入 ---
    # 78: 人物图 (Image 1)
    if "78" in workflow: workflow["78"]["inputs"]["image"] = person_image

    # 106: 衣物图 (Image 2)
    if "106" in workflow: workflow["106"]["inputs"]["image"] = clothing_image

    # 108: 配饰图 (Image 3)
    # 如果没有传配饰图，为了保证工作流不报错，通常保持原样或指向一个空白图
    if "108" in workflow and accessory_image:
        workflow["108"]["inputs"]["image"] = accessory_image

    # --- 映射提示词 ---
    # 111: 正向提示词编码
    if "111" in workflow:
        default_prompt = "把图片2中的衣服穿到图片1中人物身上，戴上图3的耳饰，尺寸很小。保留图片1中人物其他特征"
        workflow["111"]["inputs"]["prompt"] = prompt_text if prompt_text else default_prompt

    # 110: 负向提示词 (同步图片引用，确保 Qwen 模型上下文正确)
    if "110" in workflow:
        workflow["110"]["inputs"]["image1"] = workflow["111"]["inputs"]["image1"]
        workflow["110"]["inputs"]["image2"] = workflow["111"]["inputs"]["image2"]
        workflow["110"]["inputs"]["image3"] = workflow["111"]["inputs"]["image3"]

    # --- 映射模型参数 ---
    # 如果 model_type 是 "2509" (对应你 JSON 中的 safetensors)
    if model_type == "2509":
        if "37" in workflow: workflow["37"]["inputs"]["unet_name"] = "qwen_image_edit_2509_fp8_e4m3fn.safetensors"
        if "89" in workflow: workflow["89"]["inputs"]["lora_name"] = "Qwen-Image-Edit-Lightning-4steps-V1.0.safetensors"

    # 设置保存前缀
    if "60" in workflow:
        workflow["60"]["inputs"]["filename_prefix"] = f"QwenEdit_{int(time.time())}"

    return workflow


comfyui_client = ComfyUIClient(server_address="http://127.0.0.1:8188")
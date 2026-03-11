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
    def __init__(self, server_address: str = "http://127.0.0.1:8118"):
        # 默认指向你测试成功的 8118 端口
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        # ✨ 创建一个绕过系统代理的 Session，防止“梯子”干扰
        self.session = requests.Session()
        self.session.trust_env = False

    def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        try:
            payload = {"prompt": prompt, "client_id": self.client_id}
            response = self.session.post(
                f"{self.server_address}/prompt",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10 
            )
            if response.status_code == 200:
                return response.json().get("prompt_id")
            # 记录 ComfyUI 返回的具体错误
            logger.error(f"ComfyUI 拒绝请求: {response.text}")
            return None
        except Exception as e:
            logger.error(f"提交任务失败: {str(e)}")
            raise HTTPException(status_code=503, detail="ComfyUI服务连接失败")

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
            if not filename: filename = f"upload_{int(time.time())}.png"
            files = {"image": (filename, image_data)}
            data = {"type": type}
            # 💡 强制切断代理干扰
            response = self.session.post(
                f"{self.server_address}/upload/image", 
                files=files, 
                data=data,
                proxies={"http": None, "https": None}, 
                timeout=10
            )
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
        # 👇 移除了 accessory_image 参数，因为新工作流不支持
        model_type: str = "2509",
        prompt_text: str = ""
) -> Dict[str, Any]:
    """
    根据新的【两图输入】工作流 JSON 构建任务 (节点 78, 106)
    """
    # 确保模板文件存在
    template_path = os.path.join(os.path.dirname(__file__), "qwen_edit_v1.json")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
    except Exception as e:
        logger.error(f"加载模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"工作流模板丢失或JSON格式错误: {str(e)}")

    # --- 1. 映射图片输入 ---
    # 78: 人物图 (Image 1)
    if "78" in workflow: 
        workflow["78"]["inputs"]["image"] = person_image
    else:
        logger.error("工作流 JSON 缺少节点 78 (人物图加载器)")

    # 106: 衣物图 (Image 2)
    if "106" in workflow: 
        workflow["106"]["inputs"]["image"] = clothing_image
    else:
        logger.error("工作流 JSON 缺少节点 106 (衣物图加载器)")

    # ⚠️ 注意：这里彻底移除了对节点 108 (配饰图) 的处理

    # --- 2. 映射提示词 ---
    # 111: 正向提示词编码 (TextEncodeQwenImageEditPlus)
    if "111" in workflow:
        # 移除了关于“配饰/图3”的描述
        default_prompt = "Dress the person in image1 in the clothes from image2, preserving the features of the person."
        workflow["111"]["inputs"]["prompt"] = prompt_text if prompt_text else default_prompt
        # 确保图片引用正确
        workflow["111"]["inputs"]["image1"] = ["93", 0] # 缩放后的人物图
        workflow["111"]["inputs"]["image2"] = ["106", 0] # 衣物图

    # 110: 负向提示词 (TextEncodeQwenImageEditPlus) - 确保上下文图片引用正确
    if "110" in workflow:
        workflow["110"]["inputs"]["prompt"] = "blurry, out of focus, distorted, deformed, wrong clothes, bad proportion, accessories on head"
        workflow["110"]["inputs"]["image1"] = ["93", 0]
        workflow["110"]["inputs"]["image2"] = ["106", 0]

    # --- 3. 保存图片前缀 ---
    if "60" in workflow:
        workflow["60"]["inputs"]["filename_prefix"] = f"VirtualTryOn_{int(time.time())}"

    return workflow

# 初始化全局实例
comfyui_client = ComfyUIClient(server_address="http://127.0.0.1:8118")
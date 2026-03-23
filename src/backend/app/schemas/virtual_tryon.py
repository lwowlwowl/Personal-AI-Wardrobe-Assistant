from typing import Optional

from pydantic import BaseModel, Field


class VirtualTryOnGenerateRequest(BaseModel):
    """前端 VirtualTryOn.vue 生成接口 JSON 体"""
    person_image: str = Field(..., description="已上传到 ComfyUI 的人物图文件名")
    clothing_image: str = Field(..., description="已上传到 ComfyUI 的服装图文件名")
    token: Optional[str] = Field(None, description="JWT，与衣柜接口一致")
    model_type: str = Field("2509", description="工作流模型类型标识")
    prompt: str = Field("", description="可选提示词，空则用工作流默认")


class VirtualTryOnUploadFromStorageRequest(BaseModel):
    """由本机 uploads 目录已有路径直接转 ComfyUI，避免前端 downloadFile 跨域/白名单失败"""

    image_ref: str = Field(
        ...,
        description="衣柜/模特图 URL 路径，如 /Personal-AI-Wardrobe-Assistant/uploads/1/xxx.jpg",
    )
    token: Optional[str] = Field(None, description="JWT")
    image_type: Optional[str] = Field(None, description="person / clothing，仅日志用")

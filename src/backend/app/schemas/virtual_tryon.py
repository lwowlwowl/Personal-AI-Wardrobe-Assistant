from typing import Optional

from pydantic import BaseModel, Field


class VirtualTryOnGenerateRequest(BaseModel):
    """JSON body for VirtualTryOn.vue generate endpoint."""
    person_image: str = Field(..., description="Person image filename already uploaded to ComfyUI")
    clothing_image: str = Field(..., description="Clothing image filename already uploaded to ComfyUI")
    token: Optional[str] = Field(None, description="JWT, same as wardrobe APIs")
    model_type: str = Field("2509", description="Workflow model type id")
    prompt: str = Field("", description="Optional prompt; empty uses workflow default")


class VirtualTryOnUploadFromStorageRequest(BaseModel):
    """Upload from an existing path under local uploads to ComfyUI (avoids client downloadFile issues)."""

    image_ref: str = Field(
        ...,
        description="Wardrobe/model image URL path, e.g. /Personal-AI-Wardrobe-Assistant/uploads/1/xxx.jpg",
    )
    token: Optional[str] = Field(None, description="JWT")
    image_type: Optional[str] = Field(None, description="person / clothing (logging only)")

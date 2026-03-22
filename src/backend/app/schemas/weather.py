"""天氣 API 相關 Pydantic 模型（與修改.md 對齊；路由仍可用 Query，此處供擴充/共用）。"""
from pydantic import BaseModel, ConfigDict, Field


class WeatherLatLonParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    lat: float = Field(..., description="纬度")
    lon: float = Field(..., description="经度")

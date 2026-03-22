from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import AppError
from app.services import weather_service

router = APIRouter(tags=["weather"])


@router.get("/api/weather/now")
async def get_weather_now(
    lat: float = Query(..., description="纬度"),
    lon: float = Query(..., description="经度"),
    token: Optional[str] = Query(None, description="用户认证令牌（用于按用户隔离天气地理缓存）"),
):
    try:
        return weather_service.fetch_weather_now(lat=lat, lon=lon, token=token)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from None

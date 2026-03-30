from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import AppError
from app.services import weather_service

router = APIRouter(tags=["weather"])


@router.get("/api/weather/now")
async def get_weather_now(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    token: Optional[str] = Query(None, description="Auth token (per-user geo cache for weather)"),
):
    try:
        return weather_service.fetch_weather_now(lat=lat, lon=lon, token=token)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from None

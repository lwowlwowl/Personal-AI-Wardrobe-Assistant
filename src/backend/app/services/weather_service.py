"""天氣查詢業務邏輯（QWeather、地理快取、短時快取）；路由層只負責轉 HTTP。"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Union

import app.crud as crud
from AIwardrobe.services.weather_cache import (
    get_cached_location_by_coords,
    set_user_location_cache,
)
from AIwardrobe.utils.fetch_weather_json import (
    fetch_weather_json_now,
    get_location_all_by_coords,
)

from app.core.exceptions import AppError

_log = logging.getLogger(__name__)

_WEATHER_CACHE_TTL_SEC = 30 * 60
_weather_cache: Dict[str, Dict[str, Any]] = {}


def _wind_scale_to_desc(scale: str) -> str:
    try:
        n = int(scale or "0")
    except (ValueError, TypeError):
        return "—"
    if n <= 2:
        return "Light Breeze"
    if n <= 4:
        return "Moderate Breeze"
    if n <= 6:
        return "Strong Breeze"
    if n <= 8:
        return "Near Gale"
    if n <= 10:
        return "Gale"
    return "Storm"


def fetch_weather_now(lat: float, lon: float, token: Optional[str]) -> Dict[str, Any]:
    """
    取得當前天氣摘要（與原 /api/weather/now 回應一致）。
    失敗時拋 AppError（對應原 HTTPException 的 status 與 detail 文案）。
    """
    host = (os.environ.get("QWEATHER_API_HOST") or "").strip().lower()
    if "api.qweather.com" in host and "qweatherapi.com" not in host:
        raise AppError(
            status_code=400,
            message=(
                "QWEATHER_API_HOST 不能使用 api.qweather.com（会 403）。"
                "请登录 https://dev.qweather.com 控制台，在项目/认证里复制「API Host」专属域名（形如 https://xxx.def.qweatherapi.com），"
                "填到 backend/.env 的 QWEATHER_API_HOST，保存后重启后端。"
            ),
        )

    cache_user_id: Union[int, str] = "anonymous"
    if token:
        payload = crud.verify_access_token(token)
        if not payload or not payload.get("user_id"):
            raise AppError(status_code=401, message="无效或过期的token")
        cache_user_id = payload["user_id"]

    location = get_cached_location_by_coords(cache_user_id, lat, lon, lang="en")
    if not location:
        try:
            location = get_location_all_by_coords(lat, lon, lang="en")
        except (RuntimeError, ValueError) as e:
            raise AppError(status_code=400, message=str(e)) from e
        if not location:
            raise AppError(status_code=400, message="未匹配到该经纬度位置，请检查坐标")
        set_user_location_cache(cache_user_id, lat, lon, location, lang="en")

    location_id = location.get("id")
    if not location_id:
        raise AppError(status_code=400, message="未匹配到该经纬度位置，请检查坐标")

    cache_key = location_id
    now_ts = time.time()
    if cache_key in _weather_cache:
        entry = _weather_cache[cache_key]
        if now_ts - entry["fetched_at"] < _WEATHER_CACHE_TTL_SEC:
            return entry["response"]

    try:
        data = fetch_weather_json_now(location=location_id, lang="en")
    except RuntimeError as e:
        raise AppError(status_code=400, message=str(e)) from e
    except Exception as e:
        _log.exception("天气接口异常")
        detail = f"天气服务异常: {str(e)}"
        if "403" in str(e):
            detail += "。和风 403 常见原因：请将 QWEATHER_API_HOST 改为控制台「API Host」中的专属域名（如 xxx.def.qweatherapi.com），勿用 api.qweather.com；或检查账户额度与 JWT 凭据。"
        raise AppError(status_code=500, message=detail) from e

    now = data.get("now") or {}
    temp = now.get("temp", "")
    text = now.get("text", "")
    wind_scale = now.get("windScale", "")
    wind_desc = _wind_scale_to_desc(wind_scale)

    response = {
        "temp": temp,
        "text": text,
        "windScale": wind_scale,
        "windDesc": wind_desc,
    }
    _weather_cache[cache_key] = {"response": response, "fetched_at": now_ts}
    return response

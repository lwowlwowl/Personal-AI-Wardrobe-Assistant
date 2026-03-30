"""Weather lookup (QWeather, geo cache, short TTL cache); HTTP is handled in routes only."""
from __future__ import annotations

import os
import traceback
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
    Return current-weather summary (same shape as legacy /api/weather/now).
    On failure raises AppError (status/detail aligned with former HTTPException).
    """
    host = (os.environ.get("QWEATHER_API_HOST") or "").strip().lower()
    if "api.qweather.com" in host and "qweatherapi.com" not in host:
        raise AppError(
            status_code=400,
            message=(
                "QWEATHER_API_HOST cannot use api.qweather.com (it causes HTTP 403). "
                "Sign in to https://dev.qweather.com, copy your dedicated 'API Host' domain "
                "(for example, https://xxx.def.qweatherapi.com), put it into backend/.env as "
                "QWEATHER_API_HOST, then restart the backend."
            ),
        )

    cache_user_id: Union[int, str] = "anonymous"
    if token:
        payload = crud.verify_access_token(token)
        if not payload or not payload.get("user_id"):
            raise AppError(status_code=401, message="Invalid or expired token")
        cache_user_id = payload["user_id"]

    location = get_cached_location_by_coords(cache_user_id, lat, lon, lang="en")
    if not location:
        try:
            location = get_location_all_by_coords(lat, lon, lang="en")
        except (RuntimeError, ValueError) as e:
            raise AppError(status_code=400, message=str(e)) from e
        if not location:
            raise AppError(status_code=400, message="No location matched these coordinates. Please check latitude/longitude")
        set_user_location_cache(cache_user_id, lat, lon, location, lang="en")

    location_id = location.get("id")
    if not location_id:
        raise AppError(status_code=400, message="No location matched these coordinates. Please check latitude/longitude")

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
        print(f"fetch_weather_now unexpected error:\n{traceback.format_exc()}")
        detail = f"Weather service error: {str(e)}"
        if "403" in str(e):
            detail += (
                ". Common QWeather 403 causes: set QWEATHER_API_HOST to your dedicated "
                "'API Host' domain from the dashboard (for example, xxx.def.qweatherapi.com) "
                "instead of api.qweather.com, and check account quota and JWT credentials."
            )
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

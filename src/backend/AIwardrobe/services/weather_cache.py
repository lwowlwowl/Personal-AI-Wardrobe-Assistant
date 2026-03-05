import time
from typing import Any


_COORD_LOCATION_CACHE_TTL_SEC = 30 * 60
_coord_location_cache: dict[str, dict[str, Any]] = {}


def _build_coord_cache_key(
    user_id: int | str,
    lat: float,
    lon: float,
    lang: str | None,
) -> str:
    return f"{user_id}:{round(lat, 3)},{round(lon, 3)}:{lang or ''}"


def set_user_location_cache(
    user_id: int | str,
    lat: float,
    lon: float,
    location: dict[str, Any],
    lang: str | None = "en",
) -> None:
    cache_key = _build_coord_cache_key(user_id, lat, lon, lang)
    _coord_location_cache[cache_key] = {
        "location": location,
        "fetched_at": time.time(),
    }


def get_cached_location_by_coords(
    user_id: int | str,
    lat: float,
    lon: float,
    lang: str | None = "en",
) -> dict[str, Any] | None:
    cache_key = _build_coord_cache_key(user_id, lat, lon, lang)
    cached = _coord_location_cache.get(cache_key)
    if not cached:
        return None

    if time.time() - cached["fetched_at"] >= _COORD_LOCATION_CACHE_TTL_SEC:
        _coord_location_cache.pop(cache_key, None)
        return None
    return cached["location"]


def get_user_location_cache(user_id: int | str) -> list[dict[str, Any]]:
    prefix = f"{user_id}:"
    now_ts = time.time()
    rows: list[dict[str, Any]] = []

    for cache_key in list(_coord_location_cache.keys()):
        if not cache_key.startswith(prefix):
            continue

        cached = _coord_location_cache.get(cache_key)
        if not cached:
            continue

        if now_ts - cached["fetched_at"] >= _COORD_LOCATION_CACHE_TTL_SEC:
            _coord_location_cache.pop(cache_key, None)
            continue

        raw_key = cache_key[len(prefix):]
        coord_part, _, lang_part = raw_key.partition(":")
        rows.append(
            {
                "coords": coord_part,
                "lang": lang_part,
                "fetched_at": cached["fetched_at"],
                "location": cached["location"],
            }
        )

    return rows


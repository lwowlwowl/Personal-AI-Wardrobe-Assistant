import json
import os
import time
from typing import Any

import jwt
import requests

from AIwardrobe.utils.config_handler import load_env_config


load_env_config()
DEFAULT_HOST = os.getenv("QWEATHER_API_HOST")


def _format_location_text(location: dict[str, Any]) -> str:
    """
    Build a concise human-readable location summary.
    """
    name = location.get("name") or ""
    adm2 = location.get("adm2") or ""
    adm1 = location.get("adm1") or ""
    country = location.get("country") or ""
    location_id = location.get("id") or ""

    place_parts = [part for part in [country, adm1, adm2, name] if part]
    place = " ".join(place_parts).strip() or "Unknown place"
    return f"{place} (id: {location_id})" if location_id else place


def _extract_useful_location_fields(location: dict[str, Any]) -> dict[str, Any]:
    """
    Keep only useful location fields and provide a readable text.
    """
    useful: dict[str, Any] = {
        "id": location.get("id"),
        "name": location.get("name"),
        "adm1": location.get("adm1"),
        "adm2": location.get("adm2"),
        "country": location.get("country"),
        "tz": location.get("tz"),
        "utcOffset": location.get("utcOffset"),
    }
    useful["text"] = _format_location_text(useful)
    return useful


def _build_auth_headers() -> dict:
    """
    Build JWT auth headers.
    Returns:
        dict: {"Authorization": "Bearer <JWT>"}
    """
    kid = os.getenv("QWEATHER_KID")
    project_id = os.getenv("QWEATHER_PROJECT_ID")
    private_key_path = os.getenv("QWEATHER_PRIVATE_KEY_PATH")

    if not kid or not project_id:
        raise RuntimeError("QWEATHER_KID or QWEATHER_PROJECT_ID is not set")

    if not private_key_path:
        raise RuntimeError("QWEATHER_PRIVATE_KEY_PATH is not set")

    with open(os.path.expanduser(private_key_path), "r", encoding="utf-8") as f:
        private_key = f.read()

    now = int(time.time())
    # QWeather JWT: sub=project id, iat=now, exp=now+600; header includes kid
    payload = {
        "sub": project_id,
        "iat": now,
        "exp": now + 600,
    }
    encoded_jwt = jwt.encode(
        payload, private_key, algorithm="EdDSA", headers={"kid": kid}
    )
    return {
        "Authorization": f"Bearer {encoded_jwt}",
        "Accept-Encoding": "gzip",
    }


def _request_json(url: str, headers: dict, params: dict | None = None) -> dict:
    """
    Send GET request and parse JSON response.
    """
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _lookup_location_all(
    host: str, headers: dict, city: str, lang: str | None
) -> dict[str, Any] | None:
    """
    Lookup location id via GeoAPI by city name or coordinate.
    """
    params: dict[str, Any] = {"location": city}
    if lang:
        params["lang"] = lang

    url = f"{host}/geo/v2/city/lookup"
    resp = _request_json(url, headers, params=params)

    if resp.get("code") != "200":
        return None

    locations = resp.get("location") or []
    if not locations:
        return None

    return _extract_useful_location_fields(locations[0])

def _lookup_location_id(
    host: str, headers: dict, city: str, lang: str | None
) -> str | None:
    location = _lookup_location_all(host, headers, city, lang)
    if not location:
        return None
    return location.get("id")


def get_location_all_by_coords(
    lat: float,
    lon: float,
    lang: str | None = "en",
) -> dict[str, Any] | None:
    """
    Resolve location metadata from lat/lon only (no weather call).
    """
    host = DEFAULT_HOST
    if not host:
        raise RuntimeError("QWEATHER_API_HOST is not set; configure it in .env")
    headers = _build_auth_headers()
    # Geo API expects location as "lon,lat" with at most two decimal places each
    location_param = f"{round(lon, 2)},{round(lat, 2)}"
    return _lookup_location_all(host, headers, location_param, lang)


def get_location_id_by_coords(
    lat: float,
    lon: float,
    lang: str | None = "en",
) -> str | None:
    """
    Resolve location_id from coordinates for cache keys etc.; no weather fetch.
    """
    location = get_location_all_by_coords(lat, lon, lang=lang)
    if not location:
        return None
    return location.get("id")


def fetch_weather_json_now(
    city: str | None = "深圳",
    location: str | None = None,
    lang: str | None = None,
    host: str = DEFAULT_HOST,
) -> dict:
    """
    Fetch current weather as structured data.
    """
    headers = _build_auth_headers()
    location_id = location

    if not location_id and city:
        location_id = _lookup_location_id(host, headers, city, lang)
        if not location_id:
            raise RuntimeError("No matching city; provide a more specific city name")

    if not location_id:
        raise RuntimeError("Neither location nor city was provided")

    params: dict[str, Any] = {"location": location_id}
    if lang:
        params["lang"] = lang

    url = f"{host}/v7/weather/now"
    now_resp = _request_json(url, headers, params=params)

    if now_resp.get("code") != "200":
        raise RuntimeError(f"QWeather API returned an error (now): {now_resp}")

    return now_resp


def fetch_weather_json_days(
    city: str | None = "深圳",
    location: str | None = None,
    lang: str | None = None,
    host: str = DEFAULT_HOST,
    days: str | None = "3d",
) -> dict:
    """
    Fetch 3,7,10,15,30 days forecast as structured data.
    """
    headers = _build_auth_headers()
    location_id = location

    if not location_id and city:
        location_id = _lookup_location_id(host, headers, city, lang)
        if not location_id:
            raise RuntimeError("No matching city; provide a more specific city name")

    if not location_id:
        raise RuntimeError("Neither location nor city was provided")

    params: dict[str, Any] = {"location": location_id}
    if lang:
        params["lang"] = lang

    url = f"{host}/v7/weather/{days}"
    daily_resp = _request_json(url, headers, params=params)

    if daily_resp.get("code") != "200":
        raise RuntimeError(f"QWeather API returned an error (forecast): {daily_resp}")

    return daily_resp


def save_weather_json(city: str | None, payload: dict, output_path: str | None = None, days: str | None = "") -> str:
    """
    Save weather payload to local JSON and return its path.
    """
    if not output_path:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            f"weather_{city}_{days}.json",
        )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output_path


def main() -> None:
    """
    Example usage for fetching and saving weather data.
    """
    lat = 39.92
    lon = 116.41

    days = ""
    # payload = fetch_weather_json_days(city,days=days)
    payload = get_location_all_by_coords(lat, lon)
    print(payload)

if __name__ == "__main__":
    main()

import json
import os
import time
from typing import Any

import jwt
import requests

from utils.config_handler import load_env_config


load_env_config()
DEFAULT_HOST = os.getenv("QWEATHER_API_HOST")


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
        raise RuntimeError("未配置QWEATHER_KID或QWEATHER_PROJECT_ID")

    if not private_key_path:
        raise RuntimeError("未配置QWEATHER_PRIVATE_KEY_PATH")

    with open(os.path.expanduser(private_key_path), "r", encoding="utf-8") as f:
        private_key = f.read()

    now = int(time.time())

    payload = {
        "sub": project_id,
        "iat": now - 30,
        "exp": now + 900,
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


def _lookup_location_id(
    host: str, headers: dict, city: str, lang: str | None
) -> str | None:
    """
    Lookup location id via GeoAPI by city name.
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

    return locations[0].get("id")


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
            raise RuntimeError("未匹配到城市，请提供更具体的城市名称")

    if not location_id:
        raise RuntimeError("未提供location或city")

    params: dict[str, Any] = {"location": location_id}
    if lang:
        params["lang"] = lang

    url = f"{host}/v7/weather/now"
    now_resp = _request_json(url, headers, params=params)

    if now_resp.get("code") != "200":
        raise RuntimeError(f"和风天气API返回异常: {now_resp}")

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
            raise RuntimeError("未匹配到城市，请提供更具体的城市名称")

    if not location_id:
        raise RuntimeError("未提供location或city")

    params: dict[str, Any] = {"location": location_id}
    if lang:
        params["lang"] = lang

    url = f"{host}/v7/weather/{days}"
    daily_resp = _request_json(url, headers, params=params)

    if daily_resp.get("code") != "200":
        raise RuntimeError(f"和风天气API返回异常:{daily_resp}")

    return daily_resp


def save_weather_json(payload: dict, output_path: str | None = None) -> str:
    """
    Save weather payload to local JSON and return its path.
    """
    if not output_path:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "weather.json",
        )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output_path


def main() -> None:
    """
    Example usage for fetching and saving weather data.
    """
    payload = fetch_weather_json_now(city="深圳")
    output_path = save_weather_json(payload)
    print(f"weather json saved to: {output_path}")


if __name__ == "__main__":
    main()

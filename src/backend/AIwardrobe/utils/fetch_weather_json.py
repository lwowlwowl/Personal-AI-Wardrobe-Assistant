import argparse
import json
import os
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

from utils.path_tool import get_abs_path
from utils.config_handler import load_env_config


def _fetch_qweather(url: str, params: dict) -> dict:
    query = urlencode(params)
    request_url = f"{url}?{query}"
    with urlopen(request_url, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _lookup_qweather_location(city: str, api_key: str) -> tuple[str | None, str | None]:
    resp = _fetch_qweather(
        "https://geoapi.qweather.com/v2/city/lookup",
        {
            "location": city,
            "key": api_key,
            "number": 1,
        },
    )
    if resp.get("code") != "200":
        return None, None

    locations = resp.get("location") or []
    if not locations:
        return None, None

    location = locations[0]
    return location.get("id"), location.get("name")


def fetch_weather_json(city: str, output_path: str) -> None:
    load_env_config()
    api_key = os.getenv("QWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("未配置QWEATHER_API_KEY")

    location_id, location_name = _lookup_qweather_location(city, api_key)
    if not location_id:
        raise RuntimeError("未匹配到城市，请提供更具体的城市名称")

    now_resp = _fetch_qweather(
        "https://api.qweather.com/v7/weather/now",
        {"location": location_id, "key": api_key},
    )
    daily_resp = _fetch_qweather(
        "https://api.qweather.com/v7/weather/3d",
        {"location": location_id, "key": api_key},
    )

    if now_resp.get("code") != "200" or daily_resp.get("code") != "200":
        raise RuntimeError(f"和风天气API返回异常: {now_resp} | {daily_resp}")

    payload = {
        "city": location_name or city,
        "location_id": location_id,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "now": now_resp.get("now") or {},
        "daily": daily_resp.get("daily") or [],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="拉取和风天气数据并保存为本地JSON")
    parser.add_argument("--city", default="深圳", help="城市名称，默认：深圳")
    args = parser.parse_args()

    output_path = get_abs_path("data/weather.json")
    fetch_weather_json(args.city, output_path)
    print(f"已写入天气数据: {output_path}")


if __name__ == "__main__":
    main()

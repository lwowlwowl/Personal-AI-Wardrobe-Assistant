import json
import os.path
from contextvars import ContextVar, Token
from datetime import datetime, timedelta, timezone
from typing import Optional

from langchain_core.tools import tool
from AIwardrobe.rag.rag_service import RagSummarizeService
from AIwardrobe.services.weather_cache import get_user_location_cache
from AIwardrobe.utils.database_retriever import build_agent_context
from AIwardrobe.utils.config_handler import agent_conf
from AIwardrobe.utils.logger_handler import logger
from AIwardrobe.utils.path_tool import get_abs_path

from AIwardrobe.utils.fetch_weather_json import fetch_weather_json_now, save_weather_json, \
    fetch_weather_json_days

rag = RagSummarizeService()
_REQUEST_USER_ID: ContextVar[Optional[int]] = ContextVar("agent_request_user_id", default=None)


def set_agent_request_user_id(user_id: Optional[int]) -> Token:
    return _REQUEST_USER_ID.set(user_id)


def reset_agent_request_user_id(token: Token) -> None:
    _REQUEST_USER_ID.reset(token)

# China timezone: ZoneInfo("Asia/Shanghai") may fail on Windows without tzdata; fall back to UTC+8
def _china_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Shanghai")
    except Exception:
        return timezone(timedelta(hours=8))


@tool(description="Retrieve reference material from the vector store")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


def _is_today_weather_data(data: dict) -> bool:
    tz = _china_tz()
    now = datetime.now(tz)
    obs_time = (data.get("now") or {}).get("obsTime")
    if not obs_time:
        return False
    try:
        obs_dt = datetime.fromisoformat(obs_time.replace("Z", "+00:00"))
        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=tz)
        age_seconds = (now - obs_dt.astimezone(tz)).total_seconds()
        return 0 <= age_seconds <= 1800   # valid if observation is within the last 30 minutes
    except Exception:
        return False


def _refresh_weather_data(city: str, days: str = "") -> None:
    if days == "":
        payload = fetch_weather_json_now(city)
        output_path = save_weather_json(city, payload)
        logger.info(f"weather json saved to: {output_path}")
        return

    payload = fetch_weather_json_days(city, days=days)
    output_path = save_weather_json(city, payload, days=days)
    logger.info(f"weather json saved to: {output_path}")



@tool(description="Read local weather JSON for the given city and return current conditions and forecast")
def get_weather(city: str, days: str = "") -> str:
    weather_path = get_abs_path(f"data/weather_{city}_{days}.json")
    if not os.path.exists(weather_path):
        logger.info("No local weather file; fetching and saving weather data")
        if days == "":
            try:
                _refresh_weather_data(city, days)
            except Exception as exc:
                logger.warning(f"[get_weather] fetch failed: {exc}")
        else:
            try:
                _refresh_weather_data(city, days)
            except Exception as exc:
                logger.warning(f"[get_weather] fetch failed: {exc}")
    try:
        with open(weather_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return "Local weather file is empty; fetch and save weather data first."
            data = json.loads(content)
    except Exception as exc:
        logger.warning(f"[get_weather] failed to read local weather file: {exc}")
        return "Failed to read local weather file; check file format."

    if not _is_today_weather_data(data):
        logger.info("Weather observation older than 30 minutes; refreshing")
        try:
            _refresh_weather_data(city, days)
        except Exception as exc:
            logger.warning(f"[get_weather] refresh failed: {exc}")

        try:
            with open(weather_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return "Local weather file is empty; fetch and save weather data first."
                data = json.loads(content)
        except Exception as exc:
            logger.warning(f"[get_weather] failed to read file after refresh: {exc}")
            return "Failed to read local weather file; check file format."

    parts = []
    parts.append(f"Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    parts.append(f"Location: {city}")
    now = data.get("now") or {}
    if now:
        parts.append(
            "Current:"
            f" obsTime:{now.get('obsTime')}"
            f" {now.get('text','unknown')}, "
            f"{now.get('temp','?')}°C, "
            f"feels like {now.get('feelsLike','?')}°C, "
            f"humidity {now.get('humidity','?')}%, "
            f"{now.get('windDir','unknown')} wind Bft {now.get('windScale','?')}, {now.get('windSpeed','?')} km/h, "
            f"precip this hour {now.get('precip','?')} mm "
            f"({now.get('obsTime','unknown time')})"
        )

    daily = data.get("daily") or []
    if daily:
        forecast_lines = []
        for day in daily:
            forecast_lines.append(
                f"{day.get('obsTime')}"
                f"{day.get('fxDate','')} "
                f"day {day.get('textDay','unknown')} max {day.get('tempMax','?')}°C "
                f"{day.get('windDirDay','unknown')} Bft {day.get('windScaleDay','?')} "
                f"{day.get('windSpeedDay','?')} km/h; "
                f"night {day.get('textNight','unknown')} min {day.get('tempMin','?')}°C "
                f"{day.get('windDirNight','unknown')} Bft {day.get('windScaleNight','?')} "
                f"{day.get('windSpeedNight','?')} km/h, "
                f"humidity {day.get('humidity','?')}%, "
                f"precip {day.get('precip','?')} mm, "
                f"UV index {day.get('uvIndex','?')}"
            )
        parts.append("Forecast: " + " | ".join(forecast_lines))

    if len(parts) <= 2 and not now and not daily:
        return "No valid weather data available."

    return "\n".join(parts)


@tool(description="Return the user's city as plain text. Uses cache from Recommendation AI page after location/weather; if missing, ask user to open that page or allow location.")
def get_user_location() -> str:
    user_id = _REQUEST_USER_ID.get()
    if user_id is None:
        return "Not logged in; cannot resolve location. Please log in and try again."
    user_locations = get_user_location_cache(user_id)
    if not user_locations:
        return (
            "No location cached yet. Open the Recommendation AI page and allow location, "
            "or ask a weather-related question once to trigger geolocation, then try again."
        )
    latest = max(user_locations, key=lambda item: item.get("fetched_at", 0))
    loc = latest.get("location") or {}
    # Prefer city-level adm2 (prefecture), then name (district), then adm1 (province)
    city = (loc.get("adm2") or loc.get("name") or loc.get("adm1") or loc.get("text") or "").strip()
    return city or "Unknown city"

# @tool(description="Return the user ID as plain text")
# def get_user_id() -> str:
#     return random.choice(user_ids)

@tool(description="Return current local datetime as plain text in YYYY-MM-DD HH:MM:SS")
def get_current_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


external_data = {}

def generate_external_data():
    """
    {
        "user_id" :{
            "month":{"feature": xxx, "efficiency": xxx, ...}
            "month":{"feature": xxx, "efficiency": xxx, ...}
            "month":{"feature": xxx, "efficiency": xxx, ...}
            ...
        },
        "user_id" :{
            "month":{"feature": xxx, "efficiency": xxx, ...}
            "month":{"feature": xxx, "efficiency": xxx, ...}
            "month":{"feature": xxx, "efficiency": xxx, ...}
            ...
        },
        ...
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"External data file not found: {external_data_path}")

        with open(external_data_path, "r", encoding="utf-8") as f:
            for line in f.readlines():
                arr: list[str] = line.strip().split(",")

                user_id: str = arr[0].replace('"',"")
                feature: str = arr[1].replace('"',"")
                efficiency: str = arr[2].replace('"', "")
                consumables: str = arr[3].replace('"', "")
                comparison: str = arr[4].replace('"', "")
                time: str = arr[5].replace('"',"")

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }


@tool(description="Fetch the user's usage records from external data; return as string, or empty if not found")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data] no usage record for user_id={user_id} month={month}")
        return ""


@tool(description="Build logged-in user's closet context (redacted, paginated, summary) as a JSON string for outfit reasoning")
def get_agent_user_context(
    closet_limit: int = 100,
    closet_offset: int = 0,
    outfit_limit: int = 50,
    outfit_offset: int = 0,
    wear_history_limit: int = 100,
    wear_history_offset: int = 0,
    include_summary: bool = True,
) -> str:
    user_id = _REQUEST_USER_ID.get()
    if user_id is None:
        return json.dumps(
            {
                "error": "missing_user_context",
                "message": "Missing login session; cannot load user closet context."
            },
            ensure_ascii=False
        )

    payload = build_agent_context(
        user_id=user_id,
        closet_limit=closet_limit,
        closet_offset=closet_offset,
        outfit_limit=outfit_limit,
        outfit_offset=outfit_offset,
        wear_history_limit=wear_history_limit,
        wear_history_offset=wear_history_offset,
        include_summary=include_summary,
    )
    user_locations = get_user_location_cache(user_id)
    if user_locations:
        latest_location = max(user_locations, key=lambda item: item.get("fetched_at", 0))
        payload["user_location"] = latest_location
    else:
        payload["user_location"] = None
    return json.dumps(payload, ensure_ascii=False)



if __name__ == '__main__':
    print(get_weather("深圳","3d"))

import json
import os.path
import random
from datetime import datetime, timedelta, timezone

from langchain_core.tools import tool
from AIwardrobe.rag.rag_service import RagSummarizeService
from AIwardrobe.utils.config_handler import agent_conf
from AIwardrobe.utils.logger_handler import logger
from AIwardrobe.utils.path_tool import get_abs_path

from AIwardrobe.utils.fetch_weather_json import fetch_weather_json_now, save_weather_json, \
    fetch_weather_json_days

rag = RagSummarizeService()

# 中國時區：Windows 上若無 tzdata 則 ZoneInfo("Asia/Shanghai") 會失敗，改用 UTC+8
def _china_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Shanghai")
    except Exception:
        return timezone(timedelta(hours=8))


@tool(description="从向量存储中检索参考资料")
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
        return 0 <= age_seconds <= 1800   # 30分钟内为有效
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



@tool(description="根据用户城市或本地位置读取天气文件并返回实况与预报")
def get_weather(city: str, days: str = "") -> str:
    weather_path = get_abs_path(f"data/weather{city}{days}.json")
    if not os.path.exists(weather_path):
        logger.info("未找到本地天气文件，正在拉取并保存天气数据")
        if days == "":
            try:
                _refresh_weather_data(city, days)
            except Exception as exc:
                logger.warning(f"[get_weather]拉取天气信息失败:{exc}")
        else:
            try:
                _refresh_weather_data(city, days)
            except Exception as exc:
                logger.warning(f"[get_weather]拉取天气信息失败:{exc}")
    try:
        with open(weather_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return "本地天气文件为空，请先拉取并保存天气数据"
            data = json.loads(content)
    except Exception as exc:
        logger.warning(f"[get_weather]读取本地天气文件失败: {exc}")
        return "读取本地天气文件失败，请检查文件格式"

    if not _is_today_weather_data(data):
        logger.info("本地天气数据非30分钟内，正在刷新")
        try:
            _refresh_weather_data(city, days)
        except Exception as exc:
            logger.warning(f"[get_weather]天气数据刷新失败:{exc}")

        try:
            with open(weather_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return "本地天气文件为空，请先拉取并保存天气数据"
                data = json.loads(content)
        except Exception as exc:
            logger.warning(f"[get_weather]刷新后读取本地天气文件失败: {exc}")
            return "读取本地天气文件失败，请检查文件格式"

    parts = []
    parts.append(f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    parts.append(f"位置：{city}")
    now = data.get("now") or {}
    if now:
        parts.append(
            "实况："
            f"观测时间:{now.get('obsTime')}"
            f"{now.get('text','未知')}，"
            f"{now.get('temp','?')}℃，"
            f"体感{now.get('feelsLike','?')}℃，"
            f"湿度{now.get('humidity','?')}%，"
            f"{now.get('windDir','未知')}风{now.get('windScale','?')}级,{now.get('windSpeed','?')}km/h"
            f"当前小时累计降水量{now.get('precip','?')}mm"
            f"（{now.get('obsTime','未知时间')}）"
        )

    daily = data.get("daily") or []
    if daily:
        forecast_lines = []
        for day in daily:
            forecast_lines.append(
                f"{day.get('obsTime')}"
                f"{day.get('fxDate','')} "
                f"白天{day.get('textDay','未知')}{day.get('tempMax','?')}℃ "
                f"{day.get('windDirDay','未知')}{day.get('windScaleDay','?')}级"
                f"{day.get('windSpeedDay','?')}km/h；"
                f"夜间{day.get('textNight','未知')}{day.get('tempMin','?')}℃ "
                f"{day.get('windDirNight','未知')}{day.get('windScaleNight','?')}级"
                f"{day.get('windSpeedNight','?')}km/h，"
                f"湿度{day.get('humidity','?')}%，"
                f"降水{day.get('precip','?')}mm，"
                f"紫外线{day.get('uvIndex','?')}级"
            )
        parts.append("预报：" + " | ".join(forecast_lines))

    if len(parts) <= 2 and not now and not daily:
        return "未查询到有效天气信息"

    return "\n".join(parts)


@tool(description="获取用户所在城市名称，以纯字符串形式返回")
def get_user_location() -> str:
    return random.choice(["深圳","合肥","杭州"])

# @tool(description="获取用户ID，以纯字符串形式返回")
# def get_user_id() -> str:
#     return random.choice(user_ids)

@tool(description="获取当前日期时间，以纯字符串形式返回，格式为YYYY-MM-DD HH:MM:SS")
def get_current_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


external_data = {}

def generate_external_data():
    """
    {
        "user_id" :{
            "month":{"特征": xxx, "效率": xxx, ...}
            "month":{"特征": xxx, "效率": xxx, ...}
            "month":{"特征": xxx, "效率": xxx, ...}
            ...
        },
        "user_id" :{
            "month":{"特征": xxx, "效率": xxx, ...}
            "month":{"特征": xxx, "效率": xxx, ...}
            "month":{"特征": xxx, "效率": xxx, ...}
            ...
        },
        ...
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

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


@tool(description="从外部系统中获取用户的使用记录，以纯字符串形式返回，如果未检索到，返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return external_data[user_id][month]
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户:{user_id}在{month}的使用数据记录")
        return ""



if __name__ == '__main__':
    print(get_weather("深圳","3d"))

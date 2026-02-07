import json
import os.path
import random
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen

from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

user_ids = ["1001","1002","1003","1004","1005","1006","1007","1008","1009","1010"]


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)

def _fetch_amap_weather(city: str, extensions: str, api_key: str) -> dict:
    params = urlencode({
        "key": api_key,
        "city": city,
        "extensions": extensions,
    })
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?{params}"
    with urlopen(url, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))

@tool(description="获取指定城市的实时天气和预报，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    if not city:
        return "未提供城市名称，无法查询天气"

    api_key = os.getenv("AMAP_WEATHER_KEY")
    if not api_key:
        return "未配置AMAP_WEATHER_KEY，无法调用高德天气API"

    try:
        live_resp = _fetch_amap_weather(city, "base", api_key)
        forecast_resp = _fetch_amap_weather(city, "all", api_key)
    except Exception as exc:
        logger.warning(f"[get_weather]调用高德天气API失败: {exc}")
        return "天气服务暂时不可用，请稍后再试"

    if live_resp.get("status") != "1" or forecast_resp.get("status") != "1":
        logger.warning(f"[get_weather]高德天气API返回异常: {live_resp} | {forecast_resp}")
        return "天气服务返回异常，请稍后再试"

    parts = []
    parts.append(f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    lives = live_resp.get("lives") or []
    if lives:
        live = lives[0]
        parts.append(
            "实况："
            f"{live.get('weather','未知')}，"
            f"{live.get('temperature','?')}℃，"
            f"湿度{live.get('humidity','?')}%，"
            f"{live.get('winddirection','未知')}风{live.get('windpower','?')}级"
            f"（{live.get('reporttime','未知时间')}）"
        )

    forecasts = forecast_resp.get("forecasts") or []
    if forecasts:
        casts = forecasts[0].get("casts") or []
        if casts:
            forecast_lines = []
            for cast in casts:
                forecast_lines.append(
                    f"{cast.get('date','')} "
                    f"周{cast.get('week','')} "
                    f"白天{cast.get('dayweather','未知')}{cast.get('daytemp','?')}℃ "
                    f"{cast.get('daywind','未知')}{cast.get('daypower','?')}级；"
                    f"夜间{cast.get('nightweather','未知')}{cast.get('nighttemp','?')}℃ "
                    f"{cast.get('nightwind','未知')}{cast.get('nightpower','?')}级"
                )
            parts.append("预报：" + " | ".join(forecast_lines))

    if len(parts) == 1:
        return "未查询到有效天气信息"

    return "\n".join(parts)

@tool(description="获取用户所在城市名称，以纯字符串形式返回")
def get_user_location() -> str:
    return random.choice(["深圳","合肥","杭州"])

@tool(description="获取用户ID，以纯字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)

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


@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"



if __name__ == '__main__':
    print(fetch_external_data("1001","2025-01"))
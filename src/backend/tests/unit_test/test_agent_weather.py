"""
Weather payload freshness logic (same as agent_tools._is_today_weather_data), kept in tests
to avoid importing LangChain. Optional ref_now pins the clock for assertions; production uses datetime.now(tz).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional


def _china_tz():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("Asia/Shanghai")
    except Exception:
        return timezone(timedelta(hours=8))


def _is_today_weather_data_logic(data: dict, ref_now: Optional[datetime] = None) -> bool:
    tz = _china_tz()
    now = datetime.now(tz) if ref_now is None else ref_now
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)

    obs_time = (data.get("now") or {}).get("obsTime")
    if not obs_time:
        return False
    try:
        obs_dt = datetime.fromisoformat(str(obs_time).replace("Z", "+00:00"))
        if obs_dt.tzinfo is None:
            obs_dt = obs_dt.replace(tzinfo=tz)
        age_seconds = (now - obs_dt.astimezone(tz)).total_seconds()
        return 0 <= age_seconds <= 1800
    except Exception:
        return False


def test_is_today_weather_data_true_within_window():
    tz = timezone(timedelta(hours=8))
    ref = datetime(2026, 3, 28, 12, 0, 0, tzinfo=tz)
    obs = (ref - timedelta(minutes=10)).isoformat()
    assert _is_today_weather_data_logic({"now": {"obsTime": obs}}, ref_now=ref) is True


def test_is_today_weather_data_false_when_too_old():
    tz = timezone(timedelta(hours=8))
    ref = datetime(2026, 3, 28, 12, 0, 0, tzinfo=tz)
    obs = (ref - timedelta(hours=2)).isoformat()
    assert _is_today_weather_data_logic({"now": {"obsTime": obs}}, ref_now=ref) is False


def test_is_today_weather_data_false_missing_obs_time():
    tz = timezone(timedelta(hours=8))
    ref = datetime(2026, 3, 28, 12, 0, 0, tzinfo=tz)
    assert _is_today_weather_data_logic({}, ref_now=ref) is False
    assert _is_today_weather_data_logic({"now": {}}, ref_now=ref) is False

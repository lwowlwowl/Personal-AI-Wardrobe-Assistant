"""Chat input: reply language selection (app.utils.language_policy)."""
from app.utils.language_policy import decide_reply_language, detect_text_language


def test_detect_chinese_dominant():
    assert detect_text_language("明天去上海開會穿什麼比較合適") == "zh"


def test_detect_english_dominant():
    assert detect_text_language("What should I wear for a job interview tomorrow") == "en"


def test_decide_reply_language_short_ack_follows_history_zh():
    lang = decide_reply_language(
        "ok",
        [{"role": "user", "content": "這件外套適合冬天嗎"}],
    )
    assert lang == "zh"


def test_decide_reply_language_explicit_zh():
    assert decide_reply_language("推薦一套商務休閒", []) == "zh"

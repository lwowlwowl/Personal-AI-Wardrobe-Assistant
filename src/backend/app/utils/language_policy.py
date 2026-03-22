import re
from typing import List, Dict

CJK_RE = re.compile(r'[\u4e00-\u9fff]')
LATIN_WORD_RE = re.compile(r'[A-Za-z]+')

SHORT_ACKS_EN = {"ok", "okay", "yes", "yep", "haha", "lol", "sure"}
SHORT_ACKS_ZH = {"好", "好的", "嗯", "哈哈", "知道了", "行", "可以"}


def count_cjk_chars(text: str) -> int:
    return len(CJK_RE.findall(text or ""))


def count_latin_words(text: str) -> int:
    return len(LATIN_WORD_RE.findall(text or ""))


def detect_text_language(text: str) -> str:
    """
    返回 'zh' / 'en' / 'unknown'
    """
    text = (text or "").strip()
    if not text:
        return "en"

    cjk_count = count_cjk_chars(text)
    latin_count = count_latin_words(text)

    lower = text.lower().strip()

    # 短确认词，单独不决定语言，交给上下文
    if lower in SHORT_ACKS_EN or text in SHORT_ACKS_ZH:
        return "unknown"

    # 英文句法主导：英文单词较多，即使夹中文，也优先英语
    if latin_count >= 3 and latin_count >= cjk_count:
        return "en"

    # 中文明显占主导
    if cjk_count >= 4 and cjk_count > latin_count:
        return "zh"

    # 轻度中文也可判中文
    if cjk_count >= 2 and latin_count <= 1:
        return "zh"

    return "en"


def detect_context_language(history_messages: List[Dict]) -> str:
    """
    history_messages: [{role: 'user'/'ai', content: '...'}]
    只看最近几条 user 消息
    """
    recent_user_msgs = [
        (m.get("content") or "")
        for m in history_messages[-6:]
        if m.get("role") == "user"
    ]

    if not recent_user_msgs:
        return "en"

    zh_score = 0
    en_score = 0

    for msg in recent_user_msgs:
        lang = detect_text_language(msg)
        if lang == "zh":
            zh_score += 1
        elif lang == "en":
            en_score += 1

    return "zh" if zh_score > en_score else "en"


def decide_reply_language(current_text: str, history_messages: List[Dict]) -> str:
    current_lang = detect_text_language(current_text)

    # 当前是短确认词/无法判断 -> 继承上下文
    if current_lang == "unknown":
        return detect_context_language(history_messages)

    # 当前明显可判断，优先当前
    if current_lang in {"zh", "en"}:
        # 但如果当前超短且上下文强烈偏中文，则继承中文
        if len(current_text.strip()) <= 4:
            ctx_lang = detect_context_language(history_messages)
            if ctx_lang == "zh" and count_cjk_chars(current_text) <= 1:
                return "zh"
        return current_lang

    return detect_context_language(history_messages)

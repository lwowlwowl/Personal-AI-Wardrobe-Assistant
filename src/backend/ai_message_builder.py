import re
from typing import Optional


def is_plan(raw_text: str) -> bool:
    if not raw_text or not isinstance(raw_text, str):
        return False
    text = raw_text.strip()
    if len(text) < 120:
        return False

    keywords = [
        "下周", "一周", "周计划", "周安排", "每日搭配", "出行安排", "行程", "计划",
        "5套不重样", "5 套不重样", "outfit schedule", "schedule", "plan"
    ]

    # 结构化信号：出现多个日期/星期 token
    day_token_re = re.compile(
        r"(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|"
        r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
        r"Mon\.?|Tue\.?|Wed\.?|Thu\.?|Fri\.?|Sat\.?|Sun\.?|"
        r"Day\s*\d+|\d{1,2}[./-]\d{1,2})",
        re.I,
    )
    day_token_count = len(day_token_re.findall(text))

    # 关键：按天拆块（行首出现 day header）
    day_header_re = re.compile(
        r"^[^a-zA-Z0-9\u4e00-\u9fa5]*(?:\s*\|?\s*)?(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|"
        r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
        r"Day\s*\d+|\d{1,2}[./-]\d{1,2})",
        re.I | re.M,
    )
    day_header_count = len(day_header_re.findall(text))

    # 计划关键词（弱信号，不能单独触发 plan）
    lower = text.lower()
    has_plan_keyword = any(k.lower() in lower for k in keywords)

    # 收紧策略：
    # - 必须出现“按天拆块”的结构（day header >= 2）
    # - 再用 token/关键词做增强，避免“说明文字/能力介绍”被误判成 plan
    if day_header_count >= 2:
        return True

    # 次级兜底：如果模型输出没有严格换行，但确实大量出现 day token，
    # 仅在同时有明确计划关键词时才认为是 plan（依然比原先严格很多）
    return day_token_count >= 5 and has_plan_keyword


def _normalize_plan_day_label(token: str) -> str:
    if not token:
        return ""
    t = token.strip()
    mapping = {
        "Mon": "Monday", "Mon.": "Monday",
        "Tue": "Tuesday", "Tue.": "Tuesday",
        "Wed": "Wednesday", "Wed.": "Wednesday",
        "Thu": "Thursday", "Thu.": "Thursday",
        "Fri": "Friday", "Fri.": "Friday",
        "Sat": "Saturday", "Sat.": "Saturday",
        "Sun": "Sunday", "Sun.": "Sunday",
    }
    return mapping.get(t, t)


def _parse_plan_from_raw_text(raw_text: str) -> Optional[dict]:
    if not raw_text or not isinstance(raw_text, str):
        return None

    # 兼容模型输出的 HTML 换行（<br> / <br/> / <br />）与混合格式
    text = raw_text.replace("\r\n", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = text.strip()

    header_re = re.compile(
        r"^[^a-zA-Z0-9\u4e00-\u9fa5]*(?:\|?\s*)?(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|"
        r"Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
        r"Mon\.?|Tue\.?|Wed\.?|Thu\.?|Fri\.?|Sat\.?|Sun\.?|"
        r"Day\s*\d+|\d{1,2}[./-]\d{1,2})(?:\s*[\(|（]([^)\n）]+)[\)|）])?",
        re.I,
    )

    cat_re = re.compile(
        r"^(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|"
        r"Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)\s*[：:]\s*(.+)$",
        re.I,
    )
    pipe_re = re.compile(
        r"^(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|"
        r"Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)\s*\|\s*([^|]+)",
        re.I,
    )

    days = []
    current = None

    def push_current():
        nonlocal current
        if not current:
            return
        items = []
        note_lines = []

        for ln in current["raw_lines"]:
            # 关键：剥离大模型擅作主张加上的 markdown 粗体与行首 bullet
            clean_ln = (ln or "").replace("**", "").strip()
            clean_ln = re.sub(r"^[-•*]\s+", "", clean_ln)

            # 抽取 ID（容忍大小寫、全形冒號、空白）：(ID: 123) / (id：123) / （ID:123）
            id_match = re.search(r"[\(（]\s*id\s*[:：]\s*(\d+)\s*[\)）]", clean_ln, re.I)
            clothing_id = int(id_match.group(1)) if id_match else None
            if id_match:
                clean_ln = clean_ln[: id_match.start()].rstrip()

            m = cat_re.match(clean_ln)
            if m:
                items.append(
                    {
                        "type": m.group(1).strip(),
                        "name": m.group(2).strip()[:200],
                        "clothingId": clothing_id,
                    }
                )
                continue

            pm = pipe_re.match(clean_ln)
            if pm:
                items.append(
                    {
                        "type": pm.group(1).strip(),
                        "name": pm.group(2).strip()[:200],
                        "clothingId": clothing_id,
                    }
                )
                continue

            if clean_ln:
                note_lines.append(clean_ln)

        notes = "\n".join(note_lines).strip()[:1600]
        days.append(
            {
                "key": current["key"],
                "label": current["label"],
                "dateText": current.get("dateText"),
                "weatherText": current.get("weatherText"),
                "items": items,
                "notes": notes or None,
            }
        )
        current = None

    lines = [ln for ln in text.split("\n") if ln.strip()]
    for ln in lines:
        hm = header_re.match(ln.strip())
        if hm:
            push_current()
            label = _normalize_plan_day_label(hm.group(1))
            meta = (hm.group(2) or "").strip()
            current = {
                "key": f"{label}-{len(days)}",
                "label": label,
                "dateText": meta if re.search(r"\d{1,2}[./-]\d{1,2}", meta) else None,
                "weatherText": meta if re.search(r"(℃|°C|降水|湿度|风|晴|雨|雪)", meta) else None,
                "raw_lines": [],
            }
            # 若 day header 同行包含其它列内容（markdown table），把剩余内容也纳入解析
            rest = ln.strip()[hm.end() :].strip()
            rest = rest.lstrip("|").strip()
            if rest:
                current["raw_lines"].append(rest)
            continue
        if current:
            current["raw_lines"].append(ln)

    push_current()
    if not days:
        return None

    # intro：第一天之前的内容
    first_idx = None
    for i, ln in enumerate(text.split("\n")):
        if header_re.match(ln.strip()):
            first_idx = i
            break
    intro = ""
    if first_idx is not None and first_idx > 0:
        intro = "\n".join(text.split("\n")[:first_idx]).strip()[:800]

    return {"title": "穿搭计划", "intro": intro or None, "days": days}


def build_plan_message(raw_text: str) -> dict:
    plan = _parse_plan_from_raw_text(raw_text) or {"title": "穿搭计划", "intro": None, "days": []}
    return {
        "role": "ai",
        "renderType": "plan",
        "rawText": (raw_text or "").strip(),
        "content": plan.get("intro") or "",
        "recommendations": [],
        "plan": plan,
    }


def is_recommendation(raw_text: str) -> bool:
    if not raw_text or not isinstance(raw_text, str):
        return False
    text = raw_text.strip()
    if len(text) < 60:
        return False

    markers = [
        "①",
        "②",
        "③",
        "④",
        "⑤",
        "场景理解",
        "穿搭核心思路",
        "推荐搭配",
        "为什么这样搭",
        "可替换方案",
    ]
    if any(m in text for m in markers):
        return True

    cat = r"(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)"
    line_re = re.compile(rf"^\s*(?:-|\*|•)?\s*{cat}\s*(?:[：:]|\|)\s*\S+", re.I | re.M)
    return len(line_re.findall(text)) >= 3


def _parse_recommendation_items(raw_text: str) -> list:
    cat = r"(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)"
    kv_re = re.compile(rf"^\s*(?:-|\*|•)?\s*{cat}\s*[：:]\s*(.+)$", re.I)
    pipe_re = re.compile(rf"^\s*(?:-|\*|•)?\s*{cat}\s*\|\s*([^|]+)(?:\|\s*([^|]+))?", re.I)

    items: list[dict] = []
    for ln in (raw_text or "").replace("\r\n", "\n").split("\n"):
        s = (ln or "").replace("**", "").strip()
        if not s:
            continue

        # 抽取 ID（容忍大小寫、全形冒號、空白）：(ID: 123) / (id：123) / （ID:123）
        id_match = re.search(r"[\(（]\s*id\s*[:：]\s*(\d+)\s*[\)）]", s, re.I)
        clothing_id = int(id_match.group(1)) if id_match else None
        if id_match:
            s = s[: id_match.start()].rstrip()

        m = kv_re.match(s)
        if m:
            name = m.group(2).strip()
            if "|" in name:
                parts = [p.strip() for p in name.split("|") if p.strip()]
                if parts:
                    nm = parts[0][:200]
                    rs = parts[1][:200] if len(parts) > 1 else ""
                    items.append(
                        {
                            "type": m.group(1).strip(),
                            "name": nm,
                            "reason": rs or None,
                            "clothingId": clothing_id,
                        }
                    )
                    continue
            items.append(
                {
                    "type": m.group(1).strip(),
                    "name": name[:200],
                    "reason": None,
                    "clothingId": clothing_id,
                }
            )
            continue

        pm = pipe_re.match(s)
        if pm:
            items.append(
                {
                    "type": pm.group(1).strip(),
                    "name": pm.group(2).strip()[:200],
                    "reason": (pm.group(3).strip()[:200] if pm.group(3) else None),
                    "clothingId": clothing_id,
                }
            )
            continue
    return items


def _extract_why_this_works(raw_text: str) -> list:
    if not raw_text:
        return []
    text = raw_text.replace("\r\n", "\n")
    m = re.search(
        r"(?:④|4)\s*.*?(为什么这样搭|why\s+this\s+works|styling\s+rationale)[：:]*\s*([\s\S]*?)(?=(?:^|\n)\s*(?:⑤|5)\s*|$)",
        text,
        re.I,
    )
    block = ""
    if m:
        block = m.group(2) or ""
    else:
        m2 = re.search(
            r"(为什么这样搭|why\s+this\s+works|styling\s+rationale)[：:]*\s*([\s\S]*?)(?=(可替换方案|alternatives|(?:^|\n)\s*(?:⑤|5)\s*)|$)",
            text,
            re.I,
        )
        if m2:
            block = m2.group(2) or ""

    block = block.strip()
    if not block:
        return []

    lines = [ln.strip(" -•\t").strip() for ln in block.split("\n") if ln.strip()]
    bullets = []
    for ln in lines:
        if ln in ["颜色逻辑", "版型逻辑", "风格逻辑"] or ln.lower() in ["color", "silhouette", "style"]:
            continue
        if len(ln) < 6:
            continue
        bullets.append(ln[:200])
        if len(bullets) >= 3:
            break
    if bullets:
        return bullets

    sentences = [s.strip() for s in re.split(r"[。；;]\s*", block) if s.strip()]
    return [s[:200] for s in sentences[:3]]


def build_recommendation_message(raw_text: str) -> dict:
    raw = (raw_text or "").strip()
    items = []

    rec_block = None
    # 只把「行首的 ③/3 推荐搭配」當作章節開頭；④/⑤ 也必須出現在新行開頭才會截斷，
    # 避免誤把 ID: 42 / 45 等數字當成下一章開始。
    m = re.search(
        r"(?:^|\n)\s*(?:③|3)\s*.*?推荐搭配[：:]*\s*([\s\S]*?)(?=(?:^|\n)\s*(?:④|4)\s*|(?:^|\n)\s*(?:⑤|5)\s*|$)",
        raw,
        re.I,
    )
    if m:
        rec_block = m.group(1)
    else:
        m2 = re.search(
            r"推荐搭配[：:]*\s*([\s\S]*?)(?=为什么这样搭|(?:^|\n)\s*(?:④|4)\s*|(?:^|\n)\s*(?:⑤|5)\s*|$)",
            raw,
            re.I,
        )
        if m2:
            rec_block = m2.group(1)

    if rec_block:
        items = _parse_recommendation_items(rec_block)
    if not items:
        items = _parse_recommendation_items(raw)

    if not items:
        return build_text_message(raw)

    intro = ""
    idx = raw.find("推荐搭配")
    if idx > 0:
        intro = re.sub(r"\s+", " ", raw[:idx].strip())[:800]

    why_this_works = _extract_why_this_works(raw)

    rec = {
        "title": "",
        "temperature": "",
        "styleTags": [],
        "content": "",
        "items": [{"type": it["type"], "name": it["name"], "reason": it.get("reason"), "clothingId": it.get("clothingId")} for it in items],
        "whyThisWorks": why_this_works,
        "cautions": [],
        "images": [],
    }

    render_type = "mixed" if intro else "recommendation"
    return {
        "role": "ai",
        "renderType": render_type,
        "rawText": raw,
        "content": intro if intro else "",
        "recommendations": [rec],
        "plan": None,
    }


def build_text_message(raw_text: str) -> dict:
    raw = (raw_text or "").strip()
    return {
        "role": "ai",
        "renderType": "text",
        "rawText": raw,
        "content": raw,
        "recommendations": [],
        "plan": None,
    }


def build_ai_message(raw_text: str) -> dict:
    raw = (raw_text or "").strip()
    if is_plan(raw):
        return build_plan_message(raw)
    if is_recommendation(raw):
        return build_recommendation_message(raw)
    return build_text_message(raw)


from __future__ import annotations

import re
from typing import Optional

# code -> (display tag, extra keywords)
REGIONS: dict[str, dict] = {
    "US": {
        "tag": "🇺🇸 美国",
        "keywords": [
            "united states",
            "unitedstates",
            "america",
            "usa",
            "美国",
            "美國",
            "美西",
            "美东",
            "美東",
            "硅谷",
            "洛杉矶",
            "洛杉磯",
            "三藩市",
            "旧金山",
            "舊金山",
            "圣何塞",
            "聖何塞",
            "芝加哥",
            "纽约",
            "紐約",
            "达拉斯",
            "達拉斯",
            "西雅图",
            "西雅圖",
            "迈阿密",
            "邁阿密",
            "华盛顿",
            "華盛頓",
            "丹佛",
            "亚特兰大",
            "亞特蘭大",
            "phoenix",
            "los angeles",
            "san jose",
            "san francisco",
            "new york",
            "seattle",
            "chicago",
            "dallas",
            "miami",
            "ashburn",
            "sanjose",
            "siliconvalley",
        ],
        "tokens": {"us", "usa"},
        "emojis": {"🇺🇸"},
    },
    "HK": {
        "tag": "🇭🇰 香港",
        "keywords": ["hong kong", "hongkong", "香港"],
        "tokens": {"hk"},
        "emojis": {"🇭🇰"},
    },
    "TW": {
        "tag": "🇹🇼 台湾",
        "keywords": ["taiwan", "台湾", "台灣", "台北", "新北", "高雄"],
        "tokens": {"tw"},
        "emojis": {"🇹🇼", "🇨🇳"},
    },
    "JP": {
        "tag": "🇯🇵 日本",
        "keywords": ["japan", "日本", "东京", "東京", "大阪", "名古屋", "tokyo", "osaka"],
        "tokens": {"jp"},
        "emojis": {"🇯🇵"},
    },
    "SG": {
        "tag": "🇸🇬 新加坡",
        "keywords": ["singapore", "新加坡", "狮城"],
        "tokens": {"sg"},
        "emojis": {"🇸🇬"},
    },
    "KR": {
        "tag": "🇰🇷 韩国",
        "keywords": ["korea", "south korea", "韩国", "韓國", "首尔", "首爾", "seoul"],
        "tokens": {"kr"},
        "emojis": {"🇰🇷"},
    },
    "GB": {
        "tag": "🇬🇧 英国",
        "keywords": ["united kingdom", "england", "london", "英国", "英國", "伦敦", "倫敦"],
        "tokens": {"gb", "uk"},
        "emojis": {"🇬🇧"},
    },
    "DE": {
        "tag": "🇩🇪 德国",
        "keywords": ["germany", "frankfurt", "德国", "德國", "法兰克福", "法蘭克福"],
        "tokens": {"de"},
        "emojis": {"🇩🇪"},
    },
    "FR": {
        "tag": "🇫🇷 法国",
        "keywords": ["france", "paris", "法国", "法國", "巴黎"],
        "tokens": {"fr"},
        "emojis": {"🇫🇷"},
    },
    "NL": {
        "tag": "🇳🇱 荷兰",
        "keywords": ["netherlands", "amsterdam", "荷兰", "荷蘭", "阿姆斯特丹"],
        "tokens": {"nl"},
        "emojis": {"🇳🇱"},
    },
    "CA": {
        "tag": "🇨🇦 加拿大",
        "keywords": ["canada", "toronto", "vancouver", "加拿大", "多伦多", "温哥华", "溫哥華"],
        "tokens": {"ca"},
        "emojis": {"🇨🇦"},
    },
    "AU": {
        "tag": "🇦🇺 澳大利亚",
        "keywords": ["australia", "sydney", "melbourne", "澳大利亚", "澳洲", "悉尼", "墨尔本"],
        "tokens": {"au"},
        "emojis": {"🇦🇺"},
    },
    "RU": {
        "tag": "🇷🇺 俄罗斯",
        "keywords": ["russia", "moscow", "俄罗斯", "俄羅斯", "莫斯科"],
        "tokens": {"ru"},
        "emojis": {"🇷🇺"},
    },
    "IN": {
        "tag": "🇮🇳 印度",
        "keywords": ["india", "mumbai", "印度", "孟买", "孟買"],
        "tokens": {"in"},
        "emojis": {"🇮🇳"},
    },
    "TH": {
        "tag": "🇹🇭 泰国",
        "keywords": ["thailand", "bangkok", "泰国", "泰國", "曼谷"],
        "tokens": {"th"},
        "emojis": {"🇹🇭"},
    },
    "VN": {
        "tag": "🇻🇳 越南",
        "keywords": ["vietnam", "越南", "胡志明", "河内", "河內"],
        "tokens": {"vn"},
        "emojis": {"🇻🇳"},
    },
    "PH": {
        "tag": "🇵🇭 菲律宾",
        "keywords": ["philippines", "manila", "菲律宾", "菲律賓", "马尼拉", "馬尼拉"],
        "tokens": {"ph"},
        "emojis": {"🇵🇭"},
    },
    "MY": {
        "tag": "🇲🇾 马来西亚",
        "keywords": ["malaysia", "kuala lumpur", "马来西亚", "馬來西亞", "吉隆坡"],
        "tokens": {"my"},
        "emojis": {"🇲🇾"},
    },
    "ID": {
        "tag": "🇮🇩 印度尼西亚",
        "keywords": ["indonesia", "jakarta", "印度尼西亚", "印尼", "雅加达", "雅加達"],
        "tokens": {"id"},
        "emojis": {"🇮🇩"},
    },
    "MO": {
        "tag": "🇲🇴 澳门",
        "keywords": ["macao", "macau", "澳门", "澳門"],
        "tokens": {"mo"},
        "emojis": {"🇲🇴"},
    },
    "CN": {
        "tag": "🇨🇳 中国",
        "keywords": ["china", "中国", "大陸", "大陆", "北京", "上海", "深圳", "广州", "廣州"],
        "tokens": {"cn"},
        "emojis": {"🇨🇳"},
    },
}

# Common ISO aliases from geo APIs
_CODE_ALIASES = {
    "UK": "GB",
    "CN": "CN",
    "USA": "US",
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\U0001F1E6-\U0001F1FF]{2}|[\u4e00-\u9fff]+")


def normalize_region_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    raw = code.strip().upper().replace(" ", "")
    raw = _CODE_ALIASES.get(raw, raw)
    if raw in REGIONS:
        return raw
    return None


def region_tag(code: str) -> str:
    return REGIONS[code]["tag"]


def infer_region_from_name(name: str) -> Optional[str]:
    if not name:
        return None
    lowered = name.lower()
    # Longer keywords first to avoid short-token ambiguity.
    ranked: list[tuple[int, str]] = []
    for code, meta in REGIONS.items():
        for kw in meta["keywords"]:
            if kw.islower() or kw.isascii() and all(c.isascii() and (c.islower() or c.isspace()) for c in kw):
                needle = kw.lower()
                if needle and needle in lowered:
                    ranked.append((len(kw), code))
            else:
                if kw in name:
                    ranked.append((len(kw), code))
        for emoji in meta["emojis"]:
            if emoji in name:
                ranked.append((4, code))
    if ranked:
        ranked.sort(key=lambda x: -x[0])
        return ranked[0][1]

    tokens = {t.lower() for t in _TOKEN_RE.findall(name)}
    for code, meta in REGIONS.items():
        if tokens & {t.lower() for t in meta["tokens"]}:
            return code
    return None


def tagged_name(name: str, code: Optional[str]) -> str:
    base = (name or "").strip() or "node"
    if not code:
        return base
    tag = region_tag(code)
    # Avoid "🇺🇸 美国 🇺🇸 美国-foo"
    if base.startswith(tag) or tag in base:
        return base
    # If the name already starts with a flag+region, keep it.
    for meta in REGIONS.values():
        if base.startswith(meta["tag"]):
            return base
    return f"{tag}-{base}"

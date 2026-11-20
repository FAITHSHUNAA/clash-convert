from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

import yaml

from .regions import infer_region_from_name, normalize_region_code, region_tag, tagged_name

GeoLookup = Callable[[str], Optional[str]]

TEST_URL = "http://www.gstatic.com/generate_204"

# Category groups keep a stable Clash Verge layout, but always fall back
# to the main proxy group instead of empty regional groups.
CATEGORY_GROUPS = [
    ("⛔️ 广告拦截", ["REJECT", "🚀 直接连接"]),
    ("🌍 国外媒体", ["🟢 Proxy"]),
    ("📺 谷歌服务", ["🟢 Proxy"]),
    ("Ⓜ️ 微软服务", ["🟢 Proxy", "🚀 直接连接"]),
    ("🤖 AIGC", ["🟢 Proxy"]),
    ("📲 电报信息", ["🟢 Proxy"]),
    ("🍎 苹果服务", ["🚀 直接连接", "🟢 Proxy"]),
    ("🐟 漏网之鱼", ["🟢 Proxy", "🚀 直接连接"]),
]


def is_ip_address(host: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, host)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except OSError:
        return False


def default_geo_lookup(ip: str, timeout: float = 3.0) -> Optional[str]:
    """Look up a country code for a literal IP. Soft-fails offline."""
    url = f"https://ipinfo.io/{ip}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "clash-convert/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    return normalize_region_code(data.get("country"))


def resolve_region(
    proxy: dict[str, Any],
    *,
    forced: Optional[str] = None,
    geo_lookup: Optional[GeoLookup] = default_geo_lookup,
) -> Optional[str]:
    if forced:
        return normalize_region_code(forced) or forced.upper()
    code = infer_region_from_name(str(proxy.get("name") or ""))
    if code:
        return code
    server = str(proxy.get("server") or "")
    if geo_lookup and is_ip_address(server):
        return geo_lookup(server)
    return None


def unique_names(proxies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, int] = {}
    out: list[dict[str, Any]] = []
    for proxy in proxies:
        item = dict(proxy)
        base = str(item.get("name") or "node")
        count = seen.get(base, 0) + 1
        seen[base] = count
        item["name"] = base if count == 1 else f"{base} {count}"
        out.append(item)
    return out


def assign_names_and_regions(
    proxies: list[dict[str, Any]],
    *,
    region: Optional[str] = None,
    geo_lookup: Optional[GeoLookup] = default_geo_lookup,
) -> tuple[list[dict[str, Any]], list[Optional[str]]]:
    named: list[dict[str, Any]] = []
    codes: list[Optional[str]] = []
    for proxy in proxies:
        item = dict(proxy)
        code = resolve_region(item, forced=region, geo_lookup=geo_lookup)
        code = normalize_region_code(code) if code else None
        item["name"] = tagged_name(str(item.get("name") or "node"), code)
        named.append(item)
        codes.append(code)
    return unique_names(named), codes


def _region_filter(code: str) -> str:
    from .regions import REGIONS

    meta = REGIONS[code]
    parts = [code, meta["tag"], *sorted(meta["tokens"], key=len, reverse=True)]
    # Keep the filter compact but enough for Clash include-all groups.
    extras = []
    for kw in meta["keywords"]:
        if not kw.isascii() or " " not in kw:
            extras.append(kw)
    # De-duplicate while preserving order
    seen = set()
    items = []
    for part in parts + extras[:8]:
        if part not in seen:
            seen.add(part)
            items.append(part)
    return "|".join(items)


def build_groups(proxies: list[dict[str, Any]], region_codes: list[Optional[str]]) -> list[dict[str, Any]]:
    names = [p["name"] for p in proxies]
    used_codes: list[str] = []
    for code in region_codes:
        if code and code not in used_codes:
            used_codes.append(code)

    groups: list[dict[str, Any]] = [
        {
            "name": "🟢 Proxy",
            "type": "select",
            "proxies": [*names, "♻️ 自动选择", *[region_tag(c) for c in used_codes], "🚀 直接连接"],
        },
        {
            "name": "♻️ 自动选择",
            "type": "url-test",
            "url": TEST_URL,
            "interval": 300,
            "tolerance": 50,
            "proxies": list(names),
        },
    ]
    for code in used_codes:
        group_nodes = [p["name"] for p, c in zip(proxies, region_codes) if c == code]
        groups.append(
            {
                "name": region_tag(code),
                "type": "url-test",
                "url": TEST_URL,
                "interval": 300,
                "tolerance": 50,
                "proxies": group_nodes,
            }
        )
    groups.append({"name": "🚀 直接连接", "type": "select", "proxies": ["DIRECT"]})
    for name, choices in CATEGORY_GROUPS:
        items = list(choices)
        # Offer real region groups after the defaults when they exist.
        if name != "⛔️ 广告拦截":
            for code in used_codes:
                tag = region_tag(code)
                if tag not in items:
                    items.append(tag)
        groups.append({"name": name, "type": "select", "proxies": items})
    return groups


def build_config(
    proxies: list[dict[str, Any]],
    *,
    region: Optional[str] = None,
    geo_lookup: Optional[GeoLookup] = default_geo_lookup,
) -> dict[str, Any]:
    if not proxies:
        raise ValueError("没有可用节点")
    named, codes = assign_names_and_regions(proxies, region=region, geo_lookup=geo_lookup)
    config: dict[str, Any] = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "ipv6": False,
        "unified-delay": True,
        "tcp-concurrent": True,
        "find-process-mode": "strict",
        "profile": {"store-selected": True, "store-fake-ip": True},
        "proxies": named,
        "proxy-groups": build_groups(named, codes),
    }
    config.update(_dns())
    config["rule-providers"] = _rule_providers()
    config["rules"] = _rules()
    return config


def dumps(config: dict[str, Any]) -> str:
    body = yaml.safe_dump(
        config,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    header = (
        "#\n"
        "# clash-convert\n"
        "# 由分享链接生成的 Clash Meta / Mihomo 配置，可直接导入 Clash Verge。\n"
        "# 使用前请打开「系统代理」或 TUN，并在 🟢 Proxy 中选中实际节点。\n"
        "# 规则模式下请用 https://ipinfo.io 等境外站点测试 IP；国内检测站常会走直连。\n"
        "#\n"
    )
    return header + body


def _dns() -> dict[str, Any]:
    return {
        "dns": {
            "enable": True,
            "ipv6": False,
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "fake-ip-filter": [
                "*.lan",
                "*.local",
                "*.localdomain",
                "*.localhost",
                "*.home.arpa",
                "+.msftncsi.com",
                "+.msftconnecttest.com",
                "time.*.com",
                "ntp.*.com",
                "+.pool.ntp.org",
            ],
            "default-nameserver": ["223.5.5.5", "119.29.29.29"],
            "nameserver": ["223.5.5.5", "119.29.29.29"],
            "proxy-server-nameserver": ["223.5.5.5", "119.29.29.29"],
        }
    }


def _http_provider(name: str, url: str, behavior: str, path: str) -> dict[str, Any]:
    return {
        "type": "http",
        "behavior": behavior,
        "format": "text",
        "url": url,
        "path": path,
        "interval": 86400,
    }


def _rule_providers() -> dict[str, Any]:
    base = "https://ruleset.skk.moe/Clash"
    blackmatrix = "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash"
    return {
        "youtube": _http_provider("youtube", f"{blackmatrix}/YouTube/YouTube.list", "classical", "./rules/youtube.list"),
        "google": _http_provider("google", f"{blackmatrix}/Google/Google.list", "classical", "./rules/google.list"),
        "reject_domainset": _http_provider("reject_domainset", f"{base}/domainset/reject.txt", "domain", "./rules/reject_domainset.txt"),
        "reject_non_ip": _http_provider("reject_non_ip", f"{base}/non_ip/reject.txt", "classical", "./rules/reject_non_ip.txt"),
        "reject_drop_non_ip": _http_provider("reject_drop_non_ip", f"{base}/non_ip/reject-drop.txt", "classical", "./rules/reject_drop_non_ip.txt"),
        "speedtest_domainset": _http_provider("speedtest_domainset", f"{base}/domainset/speedtest.txt", "domain", "./rules/speedtest_domainset.txt"),
        "cdn_domainset": _http_provider("cdn_domainset", f"{base}/domainset/cdn.txt", "domain", "./rules/cdn_domainset.txt"),
        "cdn_non_ip": _http_provider("cdn_non_ip", f"{base}/non_ip/cdn.txt", "classical", "./rules/cdn_non_ip.txt"),
        "download_domainset": _http_provider("download_domainset", f"{base}/domainset/download.txt", "domain", "./rules/download_domainset.txt"),
        "download_non_ip": _http_provider("download_non_ip", f"{base}/non_ip/download.txt", "classical", "./rules/download_non_ip.txt"),
        "icloud_private_relay_domainset": _http_provider("icloud_private_relay_domainset", f"{base}/domainset/icloud_private_relay.txt", "domain", "./rules/icloud_private_relay_domainset.txt"),
        "apple_cdn_non_ip": _http_provider("apple_cdn_non_ip", f"{base}/non_ip/apple_cdn.txt", "classical", "./rules/apple_cdn_non_ip.txt"),
        "apple_cn_non_ip": _http_provider("apple_cn_non_ip", f"{base}/non_ip/apple_cn.txt", "classical", "./rules/apple_cn_non_ip.txt"),
        "apple_services_non_ip": _http_provider("apple_services_non_ip", f"{base}/non_ip/apple_services.txt", "classical", "./rules/apple_services_non_ip.txt"),
        "microsoft_cdn_non_ip": _http_provider("microsoft_cdn_non_ip", f"{base}/non_ip/microsoft_cdn.txt", "classical", "./rules/microsoft_cdn_non_ip.txt"),
        "microsoft_non_ip": _http_provider("microsoft_non_ip", f"{base}/non_ip/microsoft.txt", "classical", "./rules/microsoft_non_ip.txt"),
        "stream_non_ip": _http_provider("stream_non_ip", f"{base}/non_ip/stream.txt", "classical", "./rules/stream_non_ip.txt"),
        "stream_ip": _http_provider("stream_ip", f"{base}/ip/stream.txt", "classical", "./rules/stream_ip.txt"),
        "telegram_non_ip": _http_provider("telegram_non_ip", f"{base}/non_ip/telegram.txt", "classical", "./rules/telegram_non_ip.txt"),
        "telegram_ip": _http_provider("telegram_ip", f"{base}/ip/telegram.txt", "classical", "./rules/telegram_ip.txt"),
        "ai_non_ip": _http_provider("ai_non_ip", f"{base}/non_ip/ai.txt", "classical", "./rules/ai_non_ip.txt"),
        "global_non_ip": _http_provider("global_non_ip", f"{base}/non_ip/global.txt", "classical", "./rules/global_non_ip.txt"),
        "domestic_non_ip": _http_provider("domestic_non_ip", f"{base}/non_ip/domestic.txt", "classical", "./rules/domestic_non_ip.txt"),
        "direct_non_ip": _http_provider("direct_non_ip", f"{base}/non_ip/direct.txt", "classical", "./rules/direct_non_ip.txt"),
        "lan_non_ip": _http_provider("lan_non_ip", f"{base}/non_ip/lan.txt", "classical", "./rules/lan_non_ip.txt"),
        "reject_ip": _http_provider("reject_ip", f"{base}/ip/reject.txt", "classical", "./rules/reject_ip.txt"),
        "lan_ip": _http_provider("lan_ip", f"{base}/ip/lan.txt", "classical", "./rules/lan_ip.txt"),
        "domestic_ip": _http_provider("domestic_ip", f"{base}/ip/domestic.txt", "classical", "./rules/domestic_ip.txt"),
        "china_ip": _http_provider("china_ip", f"{base}/ip/china_ip.txt", "classical", "./rules/china_ip.txt"),
    }


def _rules() -> list[str]:
    return [
        "RULE-SET,youtube,📺 谷歌服务",
        "RULE-SET,reject_domainset,⛔️ 广告拦截",
        "RULE-SET,reject_non_ip,⛔️ 广告拦截",
        "RULE-SET,reject_drop_non_ip,REJECT-DROP",
        "RULE-SET,speedtest_domainset,🟢 Proxy",
        "RULE-SET,cdn_domainset,🟢 Proxy",
        "RULE-SET,cdn_non_ip,🟢 Proxy",
        "RULE-SET,download_domainset,🟢 Proxy",
        "RULE-SET,download_non_ip,🟢 Proxy",
        "RULE-SET,icloud_private_relay_domainset,🍎 苹果服务",
        "RULE-SET,apple_cdn_non_ip,🍎 苹果服务",
        "RULE-SET,apple_cn_non_ip,🍎 苹果服务",
        "RULE-SET,apple_services_non_ip,🍎 苹果服务",
        "RULE-SET,microsoft_cdn_non_ip,DIRECT",
        "RULE-SET,microsoft_non_ip,Ⓜ️ 微软服务",
        "RULE-SET,stream_non_ip,🌍 国外媒体",
        "RULE-SET,stream_ip,🌍 国外媒体",
        "RULE-SET,telegram_non_ip,📲 电报信息",
        "RULE-SET,telegram_ip,📲 电报信息",
        "PROCESS-NAME,Telegram,📲 电报信息",
        "RULE-SET,ai_non_ip,🤖 AIGC",
        "RULE-SET,google,📺 谷歌服务",
        "RULE-SET,global_non_ip,🟢 Proxy",
        "RULE-SET,domestic_non_ip,DIRECT",
        "RULE-SET,direct_non_ip,DIRECT",
        "RULE-SET,lan_non_ip,DIRECT",
        "RULE-SET,reject_ip,REJECT-DROP",
        "RULE-SET,lan_ip,DIRECT",
        "RULE-SET,domestic_ip,DIRECT",
        "RULE-SET,china_ip,DIRECT",
        "GEOIP,CN,DIRECT",
        "MATCH,🐟 漏网之鱼",
    ]

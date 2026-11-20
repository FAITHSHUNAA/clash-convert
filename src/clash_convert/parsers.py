from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urlparse

SUPPORTED_SCHEMES = (
    "hysteria2",
    "hy2",
    "hysteria",
    "hy",
    "ss",
    "trojan",
    "vless",
    "vmess",
    "tuic",
)


class ParseError(ValueError):
    pass


def _b64decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _b64decode_str(data: str) -> str:
    return _b64decode(data.strip()).decode("utf-8", errors="strict")


def _truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _first(qs: dict[str, list[str]], *keys: str) -> Optional[str]:
    for key in keys:
        values = qs.get(key)
        if values and values[0] != "":
            return values[0]
        # case-insensitive
        for k, v in qs.items():
            if k.lower() == key.lower() and v and v[0] != "":
                return v[0]
    return None


def _alpn_list(raw: Optional[str]) -> Optional[list[str]]:
    if not raw:
        return None
    items = [part.strip() for part in raw.replace("%2C", ",").split(",") if part.strip()]
    return items or None


def _skip_cert(qs: dict[str, list[str]]) -> bool:
    return any(
        _truthy(_first(qs, key) or "")
        for key in ("insecure", "allowInsecure", "allowinsecure", "skip-cert-verify", "skipCertVerify")
    )


def _split_host_port(netloc: str, default_port: Optional[int] = None) -> tuple[str, int]:
    netloc = netloc.strip()
    if netloc.startswith("["):
        end = netloc.find("]")
        if end == -1:
            raise ParseError("IPv6 地址格式不正确")
        host = netloc[1:end]
        rest = netloc[end + 1 :]
        if rest.startswith(":"):
            return host, int(rest[1:])
        if default_port is None:
            raise ParseError("缺少端口")
        return host, default_port
    if ":" in netloc:
        host, port = netloc.rsplit(":", 1)
        return host, int(port)
    if default_port is None:
        raise ParseError("缺少端口")
    return netloc, default_port


def _parse_url(link: str):
    # Keep encoded password characters intact until we unquote userinfo.
    return urlparse(link)


def parse_hysteria2(link: str) -> dict[str, Any]:
    parsed = _parse_url(link)
    if "@" not in parsed.netloc:
        raise ParseError("hysteria2 链接缺少密码或服务器")
    userinfo, hostport = parsed.netloc.rsplit("@", 1)
    password = unquote(userinfo)
    host, port = _split_host_port(hostport)
    qs = parse_qs(parsed.query)
    name = unquote(parsed.fragment) if parsed.fragment else f"hysteria2-{host}"
    proxy: dict[str, Any] = {
        "name": name,
        "type": "hysteria2",
        "server": host,
        "port": port,
        "password": password,
    }
    alpn = _alpn_list(_first(qs, "alpn"))
    if alpn:
        proxy["alpn"] = alpn
    if _skip_cert(qs):
        proxy["skip-cert-verify"] = True
    pin = _first(qs, "pinSHA256", "pin-sha256", "pin_sha256", "fingerprint")
    if pin:
        proxy["pin-sha256"] = unquote(pin)
    sni = _first(qs, "sni")
    if sni:
        proxy["sni"] = unquote(sni)
    obfs = _first(qs, "obfs")
    if obfs:
        proxy["obfs"] = unquote(obfs)
    obfs_password = _first(qs, "obfs-password", "obfsPassword", "obfs_password")
    if obfs_password:
        proxy["obfs-password"] = unquote(obfs_password)
    ports = _first(qs, "mport", "ports")
    if ports:
        proxy["ports"] = unquote(ports)
    return proxy


def parse_hysteria(link: str) -> dict[str, Any]:
    parsed = _parse_url(link)
    qs = parse_qs(parsed.query)
    if parsed.netloc:
        host, port = _split_host_port(parsed.netloc)
    else:
        raise ParseError("hysteria 链接缺少服务器")
    name = unquote(parsed.fragment) if parsed.fragment else f"hysteria-{host}"
    auth = _first(qs, "auth", "auth_str", "peer") or ""
    if parsed.username:
        auth = unquote(parsed.username)
    proxy: dict[str, Any] = {
        "name": name,
        "type": "hysteria",
        "server": host,
        "port": port,
    }
    if auth:
        proxy["auth-str"] = unquote(auth)
    protocol = _first(qs, "protocol")
    if protocol:
        proxy["protocol"] = protocol
    up = _first(qs, "upmbps", "up")
    down = _first(qs, "downmbps", "down")
    if up:
        proxy["up"] = unquote(up)
    if down:
        proxy["down"] = unquote(down)
    alpn = _alpn_list(_first(qs, "alpn"))
    if alpn:
        proxy["alpn"] = alpn
    if _skip_cert(qs):
        proxy["skip-cert-verify"] = True
    sni = _first(qs, "peer", "sni")
    if sni:
        proxy["sni"] = unquote(sni)
    return proxy


def parse_trojan(link: str) -> dict[str, Any]:
    parsed = _parse_url(link)
    if "@" not in parsed.netloc:
        raise ParseError("trojan 链接缺少密码或服务器")
    password, hostport = parsed.netloc.rsplit("@", 1)
    host, port = _split_host_port(hostport)
    qs = parse_qs(parsed.query)
    name = unquote(parsed.fragment) if parsed.fragment else f"trojan-{host}"
    proxy: dict[str, Any] = {
        "name": name,
        "type": "trojan",
        "server": host,
        "port": port,
        "password": unquote(password),
    }
    sni = _first(qs, "sni", "peer")
    if sni:
        proxy["sni"] = unquote(sni)
    if _skip_cert(qs):
        proxy["skip-cert-verify"] = True
    alpn = _alpn_list(_first(qs, "alpn"))
    if alpn:
        proxy["alpn"] = alpn
    network = _first(qs, "type", "network")
    if network and network != "tcp":
        proxy["network"] = network
        if network in {"ws", "httpupgrade"}:
            ws_opts: dict[str, Any] = {}
            path = _first(qs, "path")
            host_header = _first(qs, "host")
            if path:
                ws_opts["path"] = unquote(path)
            if host_header:
                ws_opts["headers"] = {"Host": unquote(host_header)}
            if ws_opts:
                proxy["ws-opts"] = ws_opts
    return proxy


def parse_vless(link: str) -> dict[str, Any]:
    parsed = _parse_url(link)
    if "@" not in parsed.netloc:
        raise ParseError("vless 链接缺少 UUID 或服务器")
    uuid, hostport = parsed.netloc.rsplit("@", 1)
    host, port = _split_host_port(hostport)
    qs = parse_qs(parsed.query)
    name = unquote(parsed.fragment) if parsed.fragment else f"vless-{host}"
    proxy: dict[str, Any] = {
        "name": name,
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": unquote(uuid),
    }
    flow = _first(qs, "flow")
    if flow:
        proxy["flow"] = flow
    security = (_first(qs, "security") or "none").lower()
    if security in {"tls", "reality"}:
        proxy["tls"] = True
    if security == "reality":
        reality: dict[str, Any] = {}
        pk = _first(qs, "pbk", "public-key", "publicKey")
        sid = _first(qs, "sid", "short-id", "shortId")
        if pk:
            reality["public-key"] = unquote(pk)
        if sid:
            reality["short-id"] = unquote(sid)
        if reality:
            proxy["reality-opts"] = reality
    sni = _first(qs, "sni")
    if sni:
        proxy["servername"] = unquote(sni)
    if _skip_cert(qs):
        proxy["skip-cert-verify"] = True
    fingerprint = _first(qs, "fp", "fingerprint")
    if fingerprint:
        proxy["client-fingerprint"] = unquote(fingerprint)
    network = _first(qs, "type", "network") or "tcp"
    if network != "tcp":
        proxy["network"] = network
    if network == "ws":
        ws_opts: dict[str, Any] = {}
        path = _first(qs, "path")
        host_header = _first(qs, "host")
        if path:
            ws_opts["path"] = unquote(path)
        if host_header:
            ws_opts["headers"] = {"Host": unquote(host_header)}
        if ws_opts:
            proxy["ws-opts"] = ws_opts
    elif network == "grpc":
        service = _first(qs, "serviceName", "service-name")
        if service:
            proxy["grpc-opts"] = {"grpc-service-name": unquote(service)}
    return proxy


def parse_vmess(link: str) -> dict[str, Any]:
    raw = link.split("://", 1)[1]
    # Some clients put fragment after base64
    if "#" in raw:
        raw, frag = raw.split("#", 1)
        fragment_name = unquote(frag)
    else:
        fragment_name = None
    try:
        data = json.loads(_b64decode_str(raw))
    except Exception as exc:
        raise ParseError("vmess 链接不是有效的 Base64 JSON") from exc
    host = data.get("add") or data.get("host")
    port = data.get("port")
    if not host or not port:
        raise ParseError("vmess 链接缺少服务器或端口")
    name = fragment_name or data.get("ps") or f"vmess-{host}"
    proxy: dict[str, Any] = {
        "name": name,
        "type": "vmess",
        "server": host,
        "port": int(port),
        "uuid": data.get("id"),
        "alterId": int(data.get("aid") or 0),
        "cipher": data.get("scy") or "auto",
    }
    network = data.get("net") or "tcp"
    if network != "tcp":
        proxy["network"] = network
    tls = str(data.get("tls") or "").lower()
    if tls in {"tls", "true", "1"}:
        proxy["tls"] = True
    sni = data.get("sni") or data.get("serverName")
    if sni:
        proxy["servername"] = sni
    if data.get("skip-cert-verify") or data.get("verify_cert") == False:
        proxy["skip-cert-verify"] = True
    if network == "ws":
        ws_opts: dict[str, Any] = {}
        path = data.get("path")
        host_header = data.get("host")
        if path:
            ws_opts["path"] = path
        if host_header:
            ws_opts["headers"] = {"Host": host_header}
        if ws_opts:
            proxy["ws-opts"] = ws_opts
    elif network == "grpc":
        service = data.get("path") or data.get("serviceName")
        if service:
            proxy["grpc-opts"] = {"grpc-service-name": service}
    return proxy


def parse_ss(link: str) -> dict[str, Any]:
    raw = link[5:] if link.lower().startswith("ss://") else link
    name = None
    if "#" in raw:
        raw, frag = raw.split("#", 1)
        name = unquote(frag)
    raw = raw.strip()
    # SIP002: base64(method:password)@host:port or method:password@host:port
    # Legacy: base64(method:password@host:port)
    if "@" not in raw:
        try:
            decoded = _b64decode_str(raw)
        except Exception as exc:
            raise ParseError("ss 链接无法解码") from exc
        if "#" in decoded:
            decoded, frag = decoded.split("#", 1)
            name = name or unquote(frag)
        raw = decoded
    if "@" not in raw:
        raise ParseError("ss 链接缺少服务器")
    userinfo, hostport = raw.rsplit("@", 1)
    # userinfo may itself be base64
    if ":" not in userinfo:
        try:
            userinfo = _b64decode_str(userinfo)
        except Exception as exc:
            raise ParseError("ss 链接的加密方法和密码无效") from exc
    method, password = userinfo.split(":", 1)
    host, port = _split_host_port(hostport.split("?")[0])
    query = ""
    if "?" in hostport:
        query = hostport.split("?", 1)[1]
    elif "?" in raw:
        query = raw.split("?", 1)[1]
    qs = parse_qs(query) if query else {}
    proxy: dict[str, Any] = {
        "name": name or f"ss-{host}",
        "type": "ss",
        "server": host,
        "port": port,
        "cipher": unquote(method),
        "password": unquote(password),
    }
    plugin = _first(qs, "plugin")
    if plugin:
        # plugin=obfs-local;obfs=http;obfs-host=...
        parts = unquote(plugin).split(";")
        proxy["plugin"] = parts[0]
        opts = {}
        for item in parts[1:]:
            if "=" in item:
                k, v = item.split("=", 1)
                opts[k] = v
        if opts:
            proxy["plugin-opts"] = opts
    return proxy


def parse_tuic(link: str) -> dict[str, Any]:
    parsed = _parse_url(link)
    if "@" not in parsed.netloc:
        raise ParseError("tuic 链接缺少认证信息或服务器")
    userinfo, hostport = parsed.netloc.rsplit("@", 1)
    host, port = _split_host_port(hostport)
    qs = parse_qs(parsed.query)
    if ":" in userinfo:
        uuid, password = userinfo.split(":", 1)
    else:
        uuid, password = userinfo, _first(qs, "password") or ""
    name = unquote(parsed.fragment) if parsed.fragment else f"tuic-{host}"
    proxy: dict[str, Any] = {
        "name": name,
        "type": "tuic",
        "server": host,
        "port": port,
        "uuid": unquote(uuid),
        "password": unquote(password),
    }
    sni = _first(qs, "sni")
    if sni:
        proxy["sni"] = unquote(sni)
    alpn = _alpn_list(_first(qs, "alpn"))
    if alpn:
        proxy["alpn"] = alpn
    if _skip_cert(qs):
        proxy["skip-cert-verify"] = True
    congestion = _first(qs, "congestion_control", "congestion-controller")
    if congestion:
        proxy["congestion-controller"] = unquote(congestion)
    udp_relay = _first(qs, "udp_relay_mode", "udp-relay-mode")
    if udp_relay:
        proxy["udp-relay-mode"] = unquote(udp_relay)
    return proxy


_PARSERS = {
    "hysteria2": parse_hysteria2,
    "hy2": parse_hysteria2,
    "hysteria": parse_hysteria,
    "hy": parse_hysteria,
    "ss": parse_ss,
    "trojan": parse_trojan,
    "vless": parse_vless,
    "vmess": parse_vmess,
    "tuic": parse_tuic,
}


def parse_link(link: str) -> dict[str, Any]:
    text = link.strip()
    if not text:
        raise ParseError("空链接")
    if "://" not in text:
        raise ParseError("不是分享链接")
    scheme = text.split("://", 1)[0].lower()
    parser = _PARSERS.get(scheme)
    if not parser:
        raise ParseError(f"暂不支持协议：{scheme}")
    return parser(text)


_LINK_RE = re.compile(r"(?i)\b(?:hysteria2|hy2|hysteria|hy|ss|trojan|vless|vmess|tuic)://\S+")


def extract_links(text: str) -> list[str]:
    """Pull share links out of free-form text, files, or subscription blobs."""
    raw = text.strip()
    if not raw:
        return []
    links: list[str] = []
    # Direct lines first.
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "://" in line:
            # A line may start with a scheme or contain one.
            if line.split("://", 1)[0].lower() in _PARSERS:
                links.append(line)
            else:
                links.extend(m.group(0).rstrip(".,;") for m in _LINK_RE.finditer(line))
    if links:
        return links
    # Maybe a base64 subscription of one-link-per-line.
    compact = re.sub(r"\s+", "", raw)
    if re.fullmatch(r"[A-Za-z0-9+/_-]+=*", compact) and len(compact) >= 16:
        try:
            decoded = _b64decode_str(compact)
        except Exception:
            decoded = ""
        if decoded and ("://" in decoded or any(s + "://" in decoded.lower() for s in _PARSERS)):
            return extract_links(decoded)
    return [m.group(0).rstrip(".,;") for m in _LINK_RE.finditer(raw)]

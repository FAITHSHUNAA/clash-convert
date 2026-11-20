const REGIONS = {
  US: { tag: "🇺🇸 美国", keywords: ["united states","america","usa","美国","美國","美西","美东","美東","硅谷","洛杉矶","洛杉磯","旧金山","舊金山","圣何塞","芝加哥","纽约","紐約","达拉斯","西雅图","迈阿密","华盛顿","los angeles","san jose","new york","seattle","chicago","dallas","miami","ashburn"], tokens: ["us","usa"], emojis: ["🇺🇸"] },
  HK: { tag: "🇭🇰 香港", keywords: ["hong kong","hongkong","香港"], tokens: ["hk"], emojis: ["🇭🇰"] },
  TW: { tag: "🇹🇼 台湾", keywords: ["taiwan","台湾","台灣","台北","高雄"], tokens: ["tw"], emojis: ["🇹🇼"] },
  JP: { tag: "🇯🇵 日本", keywords: ["japan","日本","东京","東京","大阪","tokyo","osaka"], tokens: ["jp"], emojis: ["🇯🇵"] },
  SG: { tag: "🇸🇬 新加坡", keywords: ["singapore","新加坡"], tokens: ["sg"], emojis: ["🇸🇬"] },
  KR: { tag: "🇰🇷 韩国", keywords: ["korea","韩国","韓國","首尔","首爾","seoul"], tokens: ["kr"], emojis: ["🇰🇷"] },
  GB: { tag: "🇬🇧 英国", keywords: ["united kingdom","england","london","英国","英國","伦敦","倫敦"], tokens: ["gb","uk"], emojis: ["🇬🇧"] },
  DE: { tag: "🇩🇪 德国", keywords: ["germany","frankfurt","德国","德國","法兰克福"], tokens: ["de"], emojis: ["🇩🇪"] },
  FR: { tag: "🇫🇷 法国", keywords: ["france","paris","法国","法國","巴黎"], tokens: ["fr"], emojis: ["🇫🇷"] },
  NL: { tag: "🇳🇱 荷兰", keywords: ["netherlands","amsterdam","荷兰","荷蘭","阿姆斯特丹"], tokens: ["nl"], emojis: ["🇳🇱"] },
  CA: { tag: "🇨🇦 加拿大", keywords: ["canada","toronto","vancouver","加拿大","多伦多","温哥华"], tokens: ["ca"], emojis: ["🇨🇦"] },
  AU: { tag: "🇦🇺 澳大利亚", keywords: ["australia","sydney","melbourne","澳大利亚","澳洲","悉尼","墨尔本"], tokens: ["au"], emojis: ["🇦🇺"] },
  RU: { tag: "🇷🇺 俄罗斯", keywords: ["russia","moscow","俄罗斯","俄羅斯","莫斯科"], tokens: ["ru"], emojis: ["🇷🇺"] },
  IN: { tag: "🇮🇳 印度", keywords: ["india","mumbai","印度","孟买"], tokens: ["in"], emojis: ["🇮🇳"] },
  TH: { tag: "🇹🇭 泰国", keywords: ["thailand","bangkok","泰国","泰國","曼谷"], tokens: ["th"], emojis: ["🇹🇭"] },
  VN: { tag: "🇻🇳 越南", keywords: ["vietnam","越南","胡志明","河内"], tokens: ["vn"], emojis: ["🇻🇳"] },
  PH: { tag: "🇵🇭 菲律宾", keywords: ["philippines","manila","菲律宾","菲律賓","马尼拉"], tokens: ["ph"], emojis: ["🇵🇭"] },
  MY: { tag: "🇲🇾 马来西亚", keywords: ["malaysia","kuala lumpur","马来西亚","吉隆坡"], tokens: ["my"], emojis: ["🇲🇾"] },
  ID: { tag: "🇮🇩 印度尼西亚", keywords: ["indonesia","jakarta","印度尼西亚","印尼","雅加达"], tokens: ["id"], emojis: ["🇮🇩"] },
  MO: { tag: "🇲🇴 澳门", keywords: ["macao","macau","澳门","澳門"], tokens: ["mo"], emojis: ["🇲🇴"] },
  CN: { tag: "🇨🇳 中国", keywords: ["china","中国","北京","上海","深圳","广州"], tokens: ["cn"], emojis: ["🇨🇳"] },
};

function inferRegion(name) {
  if (!name) return null;
  const lower = name.toLowerCase();
  let best = null;
  for (const [code, meta] of Object.entries(REGIONS)) {
    for (const kw of meta.keywords) {
      if ((kw.toLowerCase() === kw ? lower.includes(kw) : name.includes(kw)) && (!best || kw.length > best.len)) {
        best = { code, len: kw.length };
      }
    }
    for (const emoji of meta.emojis) {
      if (name.includes(emoji)) best = { code, len: 4 };
    }
  }
  if (best) return best.code;
  const tokens = new Set((name.toLowerCase().match(/[a-z0-9]+/g) || []));
  for (const [code, meta] of Object.entries(REGIONS)) {
    if (meta.tokens.some((t) => tokens.has(t))) return code;
  }
  return null;
}

function taggedName(name, code) {
  const base = (name || "node").trim() || "node";
  if (!code || !REGIONS[code]) return base;
  const tag = REGIONS[code].tag;
  if (base.startsWith(tag) || base.includes(tag)) return base;
  for (const meta of Object.values(REGIONS)) {
    if (base.startsWith(meta.tag)) return base;
  }
  return `${tag}-${base}`;
}

function isIP(host) {
  return /^(?:\d{1,3}\.){3}\d{1,3}$/.test(host) || host.includes(":");
}

async function lookupCountry(ip) {
  const urls = [
    `https://ipinfo.io/${ip}/json`,
    `https://geojs.io/v1/ip/geo/${ip}.json`,
  ];
  for (const url of urls) {
    try {
      const resp = await fetch(url, { signal: AbortSignal.timeout(3500) });
      if (!resp.ok) continue;
      const data = await resp.json();
      const code = (data.country || data.country_code || "").toUpperCase();
      if (code === "UK") return "GB";
      if (REGIONS[code]) return code;
    } catch (_) {}
  }
  return null;
}

function truthy(v) {
  return ["1", "true", "yes", "on"].includes(String(v || "").toLowerCase());
}

function parseQuery(qs) {
  const out = {};
  for (const part of qs.split("&")) {
    if (!part) continue;
    const [k, v = ""] = part.split("=");
    const key = decodeURIComponent(k);
    const val = decodeURIComponent(v.replace(/\+/g, " "));
    if (!(key.toLowerCase() in out)) out[key.toLowerCase()] = val;
  }
  return out;
}

function q(qs, ...keys) {
  for (const key of keys) {
    const got = qs[key.toLowerCase()];
    if (got) return got;
  }
  return null;
}

function splitHostPort(netloc) {
  if (netloc.startsWith("[")) {
    const end = netloc.indexOf("]");
    const host = netloc.slice(1, end);
    const rest = netloc.slice(end + 1);
    return [host, Number(rest.startsWith(":") ? rest.slice(1) : 0)];
  }
  const i = netloc.lastIndexOf(":");
  if (i === -1) throw new Error("缺少端口");
  return [netloc.slice(0, i), Number(netloc.slice(i + 1))];
}

function parseGeneric(link, type) {
  const hash = link.indexOf("#");
  let name = "";
  let rest = link;
  if (hash !== -1) {
    name = decodeURIComponent(link.slice(hash + 1));
    rest = link.slice(0, hash);
  }
  const schemeEnd = rest.indexOf("://");
  const body = rest.slice(schemeEnd + 3);
  const at = body.lastIndexOf("@");
  if (at === -1) throw new Error(`${type} 链接缺少认证信息或服务器`);
  const userinfo = body.slice(0, at);
  let hostport = body.slice(at + 1);
  let query = {};
  const qi = hostport.indexOf("?");
  if (qi !== -1) {
    query = parseQuery(hostport.slice(qi + 1));
    hostport = hostport.slice(0, qi);
  }
  const [host, port] = splitHostPort(hostport);
  return { name, userinfo: decodeURIComponent(userinfo), host, port, query };
}

function parseHysteria2(link) {
  const { name, userinfo, host, port, query } = parseGeneric(link, "hysteria2");
  const proxy = {
    name: name || `hysteria2-${host}`,
    type: "hysteria2",
    server: host,
    port,
    password: userinfo,
  };
  const alpn = q(query, "alpn");
  if (alpn) proxy.alpn = alpn.split(",").map((s) => s.trim()).filter(Boolean);
  if (truthy(q(query, "insecure", "allowinsecure", "skip-cert-verify"))) proxy["skip-cert-verify"] = true;
  const pin = q(query, "pinsha256", "pin-sha256", "pin_sha256", "fingerprint");
  if (pin) proxy["pin-sha256"] = pin;
  const sni = q(query, "sni");
  if (sni) proxy.sni = sni;
  const obfs = q(query, "obfs");
  if (obfs) proxy.obfs = obfs;
  const obfsPassword = q(query, "obfs-password", "obfspassword");
  if (obfsPassword) proxy["obfs-password"] = obfsPassword;
  return proxy;
}

function parseTrojan(link) {
  const { name, userinfo, host, port, query } = parseGeneric(link, "trojan");
  const proxy = { name: name || `trojan-${host}`, type: "trojan", server: host, port, password: userinfo };
  const sni = q(query, "sni", "peer");
  if (sni) proxy.sni = sni;
  if (truthy(q(query, "insecure", "allowinsecure"))) proxy["skip-cert-verify"] = true;
  return proxy;
}

function parseVless(link) {
  const { name, userinfo, host, port, query } = parseGeneric(link, "vless");
  const proxy = { name: name || `vless-${host}`, type: "vless", server: host, port, uuid: userinfo };
  if (q(query, "flow")) proxy.flow = q(query, "flow");
  const security = (q(query, "security") || "none").toLowerCase();
  if (security === "tls" || security === "reality") proxy.tls = true;
  if (q(query, "sni")) proxy.servername = q(query, "sni");
  if (truthy(q(query, "insecure", "allowinsecure"))) proxy["skip-cert-verify"] = true;
  const network = q(query, "type", "network") || "tcp";
  if (network !== "tcp") proxy.network = network;
  if (security === "reality") {
    const reality = {};
    if (q(query, "pbk", "public-key")) reality["public-key"] = q(query, "pbk", "public-key");
    if (q(query, "sid", "short-id")) reality["short-id"] = q(query, "sid", "short-id");
    if (Object.keys(reality).length) proxy["reality-opts"] = reality;
  }
  return proxy;
}

function parseTuic(link) {
  const { name, userinfo, host, port, query } = parseGeneric(link, "tuic");
  let uuid = userinfo, password = q(query, "password") || "";
  if (userinfo.includes(":")) [uuid, password] = userinfo.split(":");
  const proxy = { name: name || `tuic-${host}`, type: "tuic", server: host, port, uuid, password };
  if (q(query, "sni")) proxy.sni = q(query, "sni");
  if (truthy(q(query, "insecure", "allowinsecure"))) proxy["skip-cert-verify"] = true;
  return proxy;
}

function b64decode(s) {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + pad;
  const bin = atob(b64);
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function parseVmess(link) {
  let raw = link.slice("vmess://".length);
  let name;
  const hash = raw.indexOf("#");
  if (hash !== -1) {
    name = decodeURIComponent(raw.slice(hash + 1));
    raw = raw.slice(0, hash);
  }
  const data = JSON.parse(b64decode(raw));
  const host = data.add || data.host;
  const proxy = {
    name: name || data.ps || `vmess-${host}`,
    type: "vmess",
    server: host,
    port: Number(data.port),
    uuid: data.id,
    alterId: Number(data.aid || 0),
    cipher: data.scy || "auto",
  };
  if (data.net && data.net !== "tcp") proxy.network = data.net;
  if (String(data.tls || "").toLowerCase() === "tls") proxy.tls = true;
  if (data.sni) proxy.servername = data.sni;
  return proxy;
}

function parseSs(link) {
  let raw = link.slice(5);
  let name;
  const hash = raw.indexOf("#");
  if (hash !== -1) {
    name = decodeURIComponent(raw.slice(hash + 1));
    raw = raw.slice(0, hash);
  }
  if (!raw.includes("@")) raw = b64decode(raw);
  const at = raw.lastIndexOf("@");
  let userinfo = raw.slice(0, at);
  const hostport = raw.slice(at + 1).split("?")[0];
  if (!userinfo.includes(":")) userinfo = b64decode(userinfo);
  const i = userinfo.indexOf(":");
  const [host, port] = splitHostPort(hostport);
  return {
    name: name || `ss-${host}`,
    type: "ss",
    server: host,
    port,
    cipher: decodeURIComponent(userinfo.slice(0, i)),
    password: decodeURIComponent(userinfo.slice(i + 1)),
  };
}

function parseLink(link) {
  const scheme = link.split("://", 2)[0].toLowerCase();
  if (scheme === "hysteria2" || scheme === "hy2") return parseHysteria2(link);
  if (scheme === "trojan") return parseTrojan(link);
  if (scheme === "vless") return parseVless(link);
  if (scheme === "vmess") return parseVmess(link);
  if (scheme === "tuic") return parseTuic(link);
  if (scheme === "ss") return parseSs(link);
  throw new Error(`暂不支持协议：${scheme}`);
}

const LINK_RE = /\b(?:hysteria2|hy2|hysteria|hy|ss|trojan|vless|vmess|tuic):\/\/\S+/gi;

function extractLinks(text) {
  const links = [];
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const scheme = trimmed.split("://", 2)[0].toLowerCase();
    if (["hysteria2","hy2","hysteria","hy","ss","trojan","vless","vmess","tuic"].includes(scheme)) {
      links.push(trimmed);
    } else {
      const found = trimmed.match(LINK_RE);
      if (found) found.forEach((s) => links.push(s.replace(/[.,;]+$/, "")));
    }
  }
  return links;
}

function yamlScalar(value) {
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "number") return String(value);
  const s = String(value);
  if (s === "" || /[:#{}[\],&*!|>'"%@`]|^\s|\s$|^[-?].|^(?:true|false|null|yes|no|on|off)$/i.test(s)) {
    return JSON.stringify(s);
  }
  return s;
}

function yamlValue(value, indent) {
  const pad = " ".repeat(indent);
  if (Array.isArray(value)) {
    if (value.every((v) => typeof v !== "object" || v === null)) {
      return "\n" + value.map((v) => `${pad}- ${yamlScalar(v)}`).join("\n");
    }
    return "\n" + value.map((v) => `${pad}-${yamlValue(v, indent + 2).replace(/^\n/, " ")}`).join("\n");
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    return "\n" + keys.map((k) => {
      const child = value[k];
      if (child && typeof child === "object") return `${pad}${k}:${yamlValue(child, indent + 2)}`;
      return `${pad}${k}: ${yamlScalar(child)}`;
    }).join("\n");
  }
  return " " + yamlScalar(value);
}

function dumpYaml(obj) {
  return Object.keys(obj).map((k) => {
    const child = obj[k];
    if (child && typeof child === "object") return `${k}:${yamlValue(child, 2)}`;
    return `${k}: ${yamlScalar(child)}`;
  }).join("\n") + "\n";
}

const RULE_PROVIDERS = (() => {
  const base = "https://ruleset.skk.moe/Clash";
  const bm = "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash";
  const http = (url, behavior, path) => ({ type: "http", behavior, format: "text", url, path, interval: 86400 });
  return {
    youtube: http(`${bm}/YouTube/YouTube.list`, "classical", "./rules/youtube.list"),
    google: http(`${bm}/Google/Google.list`, "classical", "./rules/google.list"),
    reject_domainset: http(`${base}/domainset/reject.txt`, "domain", "./rules/reject_domainset.txt"),
    reject_non_ip: http(`${base}/non_ip/reject.txt`, "classical", "./rules/reject_non_ip.txt"),
    reject_drop_non_ip: http(`${base}/non_ip/reject-drop.txt`, "classical", "./rules/reject_drop_non_ip.txt"),
    speedtest_domainset: http(`${base}/domainset/speedtest.txt`, "domain", "./rules/speedtest_domainset.txt"),
    cdn_domainset: http(`${base}/domainset/cdn.txt`, "domain", "./rules/cdn_domainset.txt"),
    cdn_non_ip: http(`${base}/non_ip/cdn.txt`, "classical", "./rules/cdn_non_ip.txt"),
    download_domainset: http(`${base}/domainset/download.txt`, "domain", "./rules/download_domainset.txt"),
    download_non_ip: http(`${base}/non_ip/download.txt`, "classical", "./rules/download_non_ip.txt"),
    icloud_private_relay_domainset: http(`${base}/domainset/icloud_private_relay.txt`, "domain", "./rules/icloud_private_relay_domainset.txt"),
    apple_cdn_non_ip: http(`${base}/non_ip/apple_cdn.txt`, "classical", "./rules/apple_cdn_non_ip.txt"),
    apple_cn_non_ip: http(`${base}/non_ip/apple_cn.txt`, "classical", "./rules/apple_cn_non_ip.txt"),
    apple_services_non_ip: http(`${base}/non_ip/apple_services.txt`, "classical", "./rules/apple_services_non_ip.txt"),
    microsoft_cdn_non_ip: http(`${base}/non_ip/microsoft_cdn.txt`, "classical", "./rules/microsoft_cdn_non_ip.txt"),
    microsoft_non_ip: http(`${base}/non_ip/microsoft.txt`, "classical", "./rules/microsoft_non_ip.txt"),
    stream_non_ip: http(`${base}/non_ip/stream.txt`, "classical", "./rules/stream_non_ip.txt"),
    stream_ip: http(`${base}/ip/stream.txt`, "classical", "./rules/stream_ip.txt"),
    telegram_non_ip: http(`${base}/non_ip/telegram.txt`, "classical", "./rules/telegram_non_ip.txt"),
    telegram_ip: http(`${base}/ip/telegram.txt`, "classical", "./rules/telegram_ip.txt"),
    ai_non_ip: http(`${base}/non_ip/ai.txt`, "classical", "./rules/ai_non_ip.txt"),
    global_non_ip: http(`${base}/non_ip/global.txt`, "classical", "./rules/global_non_ip.txt"),
    domestic_non_ip: http(`${base}/non_ip/domestic.txt`, "classical", "./rules/domestic_non_ip.txt"),
    direct_non_ip: http(`${base}/non_ip/direct.txt`, "classical", "./rules/direct_non_ip.txt"),
    lan_non_ip: http(`${base}/non_ip/lan.txt`, "classical", "./rules/lan_non_ip.txt"),
    reject_ip: http(`${base}/ip/reject.txt`, "classical", "./rules/reject_ip.txt"),
    lan_ip: http(`${base}/ip/lan.txt`, "classical", "./rules/lan_ip.txt"),
    domestic_ip: http(`${base}/ip/domestic.txt`, "classical", "./rules/domestic_ip.txt"),
    china_ip: http(`${base}/ip/china_ip.txt`, "classical", "./rules/china_ip.txt"),
  };
})();

const RULES = [
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
];

async function buildConfig(proxies, { region, geoip }) {
  const named = [];
  const codes = [];
  for (const proxy of proxies) {
    const item = { ...proxy };
    let code = region || inferRegion(item.name);
    if (!code && geoip && isIP(item.server)) code = await lookupCountry(item.server);
    if (code && !REGIONS[code]) code = null;
    item.name = taggedName(item.name, code);
    named.push(item);
    codes.push(code || null);
  }
  const seen = {};
  for (const item of named) {
    seen[item.name] = (seen[item.name] || 0) + 1;
    if (seen[item.name] > 1) item.name = `${item.name} ${seen[item.name]}`;
  }
  const names = named.map((p) => p.name);
  const used = [...new Set(codes.filter(Boolean))];
  const groups = [
    { name: "🟢 Proxy", type: "select", proxies: [...names, "♻️ 自动选择", ...used.map((c) => REGIONS[c].tag), "🚀 直接连接"] },
    { name: "♻️ 自动选择", type: "url-test", url: "http://www.gstatic.com/generate_204", interval: 300, tolerance: 50, proxies: names },
  ];
  for (const code of used) {
    groups.push({
      name: REGIONS[code].tag,
      type: "url-test",
      url: "http://www.gstatic.com/generate_204",
      interval: 300,
      tolerance: 50,
      proxies: named.filter((_, i) => codes[i] === code).map((p) => p.name),
    });
  }
  groups.push({ name: "🚀 直接连接", type: "select", proxies: ["DIRECT"] });
  const categories = [
    ["⛔️ 广告拦截", ["REJECT", "🚀 直接连接"]],
    ["🌍 国外媒体", ["🟢 Proxy"]],
    ["📺 谷歌服务", ["🟢 Proxy"]],
    ["Ⓜ️ 微软服务", ["🟢 Proxy", "🚀 直接连接"]],
    ["🤖 AIGC", ["🟢 Proxy"]],
    ["📲 电报信息", ["🟢 Proxy"]],
    ["🍎 苹果服务", ["🚀 直接连接", "🟢 Proxy"]],
    ["🐟 漏网之鱼", ["🟢 Proxy", "🚀 直接连接"]],
  ];
  for (const [name, items] of categories) {
    const proxiesInGroup = [...items];
    if (name !== "⛔️ 广告拦截") {
      for (const code of used) {
        if (!proxiesInGroup.includes(REGIONS[code].tag)) proxiesInGroup.push(REGIONS[code].tag);
      }
    }
    groups.push({ name, type: "select", proxies: proxiesInGroup });
  }
  return {
    "mixed-port": 7890,
    "allow-lan": false,
    mode: "rule",
    "log-level": "info",
    ipv6: false,
    "unified-delay": true,
    "tcp-concurrent": true,
    "find-process-mode": "strict",
    profile: { "store-selected": true, "store-fake-ip": true },
    proxies: named,
    "proxy-groups": groups,
    dns: {
      enable: true,
      ipv6: false,
      "enhanced-mode": "fake-ip",
      "fake-ip-range": "198.18.0.1/16",
      "default-nameserver": ["223.5.5.5", "119.29.29.29"],
      nameserver: ["223.5.5.5", "119.29.29.29"],
    },
    "rule-providers": RULE_PROVIDERS,
    rules: RULES,
  };
}

let lastYaml = "";

document.getElementById("convert").addEventListener("click", async () => {
  const error = document.getElementById("error");
  const wrap = document.getElementById("output-wrap");
  const output = document.getElementById("output");
  error.style.display = "none";
  error.textContent = "";
  const links = extractLinks(document.getElementById("links").value);
  if (!links.length) {
    error.textContent = "请先粘贴至少一条分享链接。";
    error.style.display = "block";
    return;
  }
  const proxies = [];
  const skipped = [];
  for (const link of links) {
    try { proxies.push(parseLink(link)); }
    catch (err) { skipped.push(`${link.slice(0, 48)}：${err.message}`); }
  }
  if (!proxies.length) {
    error.textContent = skipped.join("\n") || "没有解析到可用节点。";
    error.style.display = "block";
    return;
  }
  const button = document.getElementById("convert");
  button.disabled = true;
  try {
    const config = await buildConfig(proxies, {
      region: document.getElementById("region").value || null,
      geoip: document.getElementById("geoip").checked,
    });
    lastYaml = (
      "# clash-convert\n" +
      "# 由分享链接生成的 Clash Meta / Mihomo 配置，可直接导入 Clash Verge。\n" +
      "# 使用前请打开「系统代理」或 TUN，并在 🟢 Proxy 中选中实际节点。\n" +
      "# 规则模式下请用 https://ipinfo.io 等境外站点测试 IP。\n" +
      dumpYaml(config)
    );
    output.textContent = lastYaml;
    wrap.style.display = "block";
    document.getElementById("download").disabled = false;
    document.getElementById("copy").disabled = false;
    if (skipped.length) {
      error.textContent = "已跳过：\n" + skipped.join("\n");
      error.style.display = "block";
    }
  } catch (err) {
    error.textContent = err.message || String(err);
    error.style.display = "block";
  } finally {
    button.disabled = false;
  }
});

document.getElementById("download").addEventListener("click", () => {
  if (!lastYaml) return;
  const blob = new Blob([lastYaml], { type: "text/yaml;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "clash-convert.yaml";
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById("copy").addEventListener("click", async () => {
  if (!lastYaml) return;
  await navigator.clipboard.writeText(lastYaml);
  const btn = document.getElementById("copy");
  btn.textContent = "已复制";
  setTimeout(() => { btn.textContent = "复制"; }, 1500);
});

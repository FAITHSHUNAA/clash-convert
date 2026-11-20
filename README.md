# clash-convert

把 `hysteria2://` 等代理分享链接，转换成可直接导入 [Clash Verge](https://github.com/clash-verge-rev/clash-verge-rev) 的 Clash Meta / Mihomo YAML。

**在线使用（点开即可转换并下载）：[https://faithshunaa.github.io/clash-convert/](https://faithshunaa.github.io/clash-convert/)**

在浏览器里粘贴分享链接，生成配置后点击「下载 YAML」。转换在你的浏览器本地完成，链接不会被上传。

常见在线转换器会套用「多地区机场」模板。如果节点名字里没有「美国」或 `US`，生成配置里的「🇺🇸 美国」分组就是空的；你看起来选了美国，流量其实走不了这个节点。本工具会：

- 正确写入 `pin-sha256`、`alpn`、`skip-cert-verify`
- 根据节点名称或服务器 IP 自动加上地区前缀
- 把**实际节点**放进 `🟢 Proxy` 和对应地区分组，避免空分组

## 安装

需要 Python 3.10+：

```bash
git clone https://github.com/FAITHSHUNAA/clash-convert.git
cd clash-convert
pip install -e .
```

不想安装命令行时，直接打开 [在线转换器](https://faithshunaa.github.io/clash-convert/)，或在本地用浏览器打开 `docs/index.html`。

## 命令行

```bash
clash-convert "hysteria2://PASSWORD@HOST:PORT?alpn=h3&insecure=1&pinSHA256=FINGERPRINT#节点名" -o config.yaml
```

也可以传入文本文件（一行一个链接），或订阅 Base64：

```bash
clash-convert examples/links.txt -o config.yaml
```

常用参数：

- `-o config.yaml`：写入文件；省略则打印到终端
- `--region US`：强制指定地区（`US`、`HK`、`JP`、`SG` 等）
- `--no-geoip`：关闭按 IP 查询地区（默认会在名称没有地区信息、且服务器是 IP 时查询）

## 导入 Clash Verge

1. 打开 Clash Verge，导入生成的 YAML
2. 打开「系统代理」，或开启 TUN 模式（TUN 通常需要管理员权限）
3. 模式选「规则」或「全局」，不要选「直连」
4. 在 `🟢 Proxy` 里选中带地区前缀的实际节点，并做一次延迟测试
5. 用 [ipinfo.io](https://ipinfo.io) 检查出口 IP

在「规则」模式下，ip138、爱站等国内检测站常常会被判成直连，测到的仍是本地 IP。这不代表节点没生效。若只想先确认节点是否可用，可临时把模式改成「全局」。

## 支持的协议

| 协议 | 分享链接 |
| --- | --- |
| Hysteria2 | `hysteria2://` `hy2://`（优先支持） |
| Hysteria | `hysteria://` `hy://` |
| Shadowsocks | `ss://` |
| Trojan | `trojan://` |
| VLESS | `vless://` |
| VMess | `vmess://` |
| TUIC | `tuic://` |

无法正确解析的协议会被跳过，而不是生成一份坏配置。

## 安全说明

分享链接里包含节点密码。不要把真实链接提交到 Git 仓库、Issue 或截图里。本仓库的示例全部是占位数据（例如 `203.0.113.10` 和全 0 UUID）。

## 开发

```bash
pip install -e ".[dev]"
pytest -q
```

## License

MIT

---

# English

Convert `hysteria2://` and other proxy share links into Clash Meta / Mihomo YAML for Clash Verge.

Unlike generic “airport” templates, this tool keeps `pin-sha256` / `alpn` / `skip-cert-verify`, tags nodes with a region, and always puts the real proxy into the `🟢 Proxy` group so a US node is actually selectable.

```bash
pip install -e .
clash-convert "hysteria2://PASSWORD@HOST:PORT?alpn=h3&insecure=1&pinSHA256=FINGERPRINT#name" -o config.yaml
```

Use the [online converter](https://faithshunaa.github.io/clash-convert/), or open `docs/index.html` locally. In rule mode, test your exit IP on a site such as [ipinfo.io](https://ipinfo.io); Chinese IP-check sites are often matched as DIRECT.

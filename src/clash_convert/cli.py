from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generate import build_config, default_geo_lookup, dumps
from .parsers import ParseError, extract_links, parse_link


def _read_inputs(values: list[str], use_stdin: bool) -> str:
    chunks: list[str] = []
    if use_stdin or not values:
        if not sys.stdin.isatty() or use_stdin:
            chunks.append(sys.stdin.read())
    for value in values:
        path = Path(value)
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
        else:
            chunks.append(value)
    return "\n".join(chunks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="clash-convert",
        description="将 hysteria2 / ss / vless / vmess / trojan 等分享链接转换为 Clash Verge 可用的 YAML 配置。",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="分享链接，或包含链接的文本文件（一行一个）。也可传入订阅 Base64。",
    )
    parser.add_argument("-o", "--output", help="输出 YAML 路径。省略则打印到标准输出。")
    parser.add_argument(
        "--region",
        help="为所有节点指定地区代码，例如 US、HK、JP。优先级高于名称和 IP 识别。",
    )
    parser.add_argument(
        "--geoip",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="当名称里没有地区信息、且服务器是 IP 时，查询 IP 地理位置（默认开启）。",
    )
    parser.add_argument("--stdin", action="store_true", help="从标准输入读取链接。")
    args = parser.parse_args(argv)

    text = _read_inputs(args.inputs, args.stdin)
    links = extract_links(text)
    if not links:
        parser.error("没有找到分享链接。请传入 hysteria2://... 或包含链接的文件。")

    proxies = []
    errors = []
    for link in links:
        try:
            proxies.append(parse_link(link))
        except ParseError as exc:
            errors.append(f"{link[:48]}… {exc}" if len(link) > 48 else f"{link}  {exc}")

    if not proxies:
        for line in errors:
            print(line, file=sys.stderr)
        return 2

    geo = default_geo_lookup if args.geoip else None
    config = build_config(proxies, region=args.region, geo_lookup=geo)
    yaml_text = dumps(config)
    if args.output:
        Path(args.output).write_text(yaml_text, encoding="utf-8")
        print(f"已写入 {args.output}（{len(proxies)} 个节点）", file=sys.stderr)
    else:
        sys.stdout.write(yaml_text)
    for line in errors:
        print(f"已跳过：{line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

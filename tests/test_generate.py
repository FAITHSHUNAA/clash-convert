import yaml

from clash_convert.generate import build_config, dumps
from clash_convert.parsers import parse_link
from clash_convert.regions import infer_region_from_name, tagged_name


HY2 = (
    "hysteria2://00000000-0000-0000-0000-000000000000@203.0.113.10:443"
    "?alpn=h3&insecure=1&allowInsecure=1"
    "&pinSHA256=0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
    "#233boy-hysteria2-203.0.113.10"
)


def test_infer_region_from_name_keywords():
    assert infer_region_from_name("233boy-hysteria2-203.0.113.10") is None
    assert infer_region_from_name("US-LosAngeles-1") == "US"
    assert infer_region_from_name("香港中转") == "HK"
    assert infer_region_from_name("🇯🇵 东京") == "JP"


def test_config_puts_node_in_proxy_and_us_group():
    proxy = parse_link(HY2)
    config = build_config([proxy], geo_lookup=lambda ip: "US")
    names = [item["name"] for item in config["proxies"]]
    assert names == ["🇺🇸 美国-233boy-hysteria2-203.0.113.10"]
    node = names[0]
    generated = {item["name"]: item for item in config["proxies"]}
    assert generated[node]["pin-sha256"].startswith("0123456789ABCDEF")
    assert generated[node]["skip-cert-verify"] is True
    assert generated[node]["alpn"] == ["h3"]

    groups = {item["name"]: item for item in config["proxy-groups"]}
    assert node in groups["🟢 Proxy"]["proxies"]
    assert groups["🟢 Proxy"]["proxies"][0] == node
    assert node in groups["🇺🇸 美国"]["proxies"]
    assert node in groups["♻️ 自动选择"]["proxies"]
    # Empty regions should not be created
    assert "🇭🇰 香港" not in groups


def test_forced_region_and_yaml_roundtrip():
    proxy = parse_link(HY2)
    config = build_config([proxy], region="US", geo_lookup=None)
    text = dumps(config)
    loaded = yaml.safe_load(text)
    assert loaded["proxies"][0]["type"] == "hysteria2"
    assert "🇺🇸 美国" in loaded["proxies"][0]["name"]


def test_tagged_name_does_not_duplicate_prefix():
    assert tagged_name("🇺🇸 美国-foo", "US") == "🇺🇸 美国-foo"

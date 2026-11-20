from clash_convert.parsers import extract_links, parse_link


HY2 = (
    "hysteria2://00000000-0000-0000-0000-000000000000@203.0.113.10:443"
    "?alpn=h3&insecure=1&allowInsecure=1"
    "&pinSHA256=0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
    "#233boy-hysteria2-203.0.113.10"
)


def test_parse_hysteria2_preserves_pin_alpn_and_insecure():
    proxy = parse_link(HY2)
    assert proxy["type"] == "hysteria2"
    assert proxy["server"] == "203.0.113.10"
    assert proxy["port"] == 443
    assert proxy["password"] == "00000000-0000-0000-0000-000000000000"
    assert proxy["alpn"] == ["h3"]
    assert proxy["skip-cert-verify"] is True
    assert proxy["pin-sha256"] == (
        "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"
    )
    assert proxy["name"] == "233boy-hysteria2-203.0.113.10"


def test_extract_links_from_text_and_subscription():
    text = "# comment\n" + HY2 + "\n"
    assert extract_links(text) == [HY2]
    # trailing punctuation should be stripped when embedded
    wrapped = f"节点：{HY2}."
    assert extract_links(wrapped) == [HY2]


def test_parse_ss_and_trojan():
    ss = parse_link("ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ@203.0.113.10:8388#demo-ss")
    assert ss["type"] == "ss"
    assert ss["cipher"] == "aes-256-gcm"
    assert ss["password"] == "password"
    assert ss["server"] == "203.0.113.10"
    assert ss["name"] == "demo-ss"

    trojan = parse_link(
        "trojan://secret@203.0.113.10:443?sni=example.com&allowInsecure=1#demo-trojan"
    )
    assert trojan["type"] == "trojan"
    assert trojan["password"] == "secret"
    assert trojan["sni"] == "example.com"
    assert trojan["skip-cert-verify"] is True

"""
生成物（HTML初稿）の機械的検証ヘルパー（requirements.md 6.9）。

外部依存を増やさないため、Rails側の OutputValidator (src/backend/app/services/
output_validator.rb) が Nokogiri で行っているのと同じ観点を、標準ライブラリの
html.parser だけで簡易に再チェックする（実装のロジックを流用せず、ブラック
ボックスの観点から独立して確認する）。
"""
from __future__ import annotations

import re
from html.parser import HTMLParser


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.tags.append((tag, attrs_dict))
        if tag == "h1":
            self.h1_count += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


EXTERNAL_REF_PATTERN = re.compile(r"https?://")


def check_standalone_html(html: str, *, max_bytes: int = 6 * 1024 * 1024) -> list[str]:
    """requirements.md 6.9 の各観点を確認し、違反した観点名のリストを返す
    （空リストなら全観点をパス）。"""
    reasons = []

    byte_size = len(html.encode("utf-8"))
    if byte_size > max_bytes:
        reasons.append(f"byte_size_exceeded({byte_size})")

    if "<script" in html.lower():
        reasons.append("script_present")

    parser = _Collector()
    parser.feed(html)

    if parser.h1_count != 1:
        reasons.append(f"h1_count_invalid({parser.h1_count})")

    for tag, attrs in parser.tags:
        if tag == "img" and not attrs.get("alt"):
            reasons.append("img_missing_alt")
        for key, value in attrs.items():
            if key.lower().startswith("on"):
                reasons.append(f"inline_event_handler({key})")
            if value and EXTERNAL_REF_PATTERN.search(value) and key.lower() not in ("data-external-ok",):
                # data: URI（画像埋め込み）はhttp(s)を含まないため誤検出しない。
                reasons.append(f"external_reference({tag}.{key})")

    return reasons

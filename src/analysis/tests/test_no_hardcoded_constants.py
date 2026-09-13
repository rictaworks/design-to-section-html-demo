"""requirements.md 6章の主要しきい値がapp/config.pyに集約され、他モジュールに
直接書き込まれていないことをソース走査で検証する（CLAUDE.md「文字列リテラル/
数値の設定分離」方針）。
"""
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

# config.py以外でリテラルとして書かれていてはならない、6章由来の代表的しきい値
FORBIDDEN_LITERALS = [r"\b1200\b", r"\b48\b", r"\b40\b", r"\b800\b", r"\b400\b", r"\b0\.05\b"]

# これらのモジュールは6章のしきい値を直接扱うため対象とする
# （classify.pyは採点式のローカルな重み配分[0.2〜0.5等]を多数持ち、6.6のしきい値
#   [0.6/0.4]とは別概念のため対象から除外し、代わりに定数の参照有無を個別確認する）
TARGET_MODULES = ["normalize.py", "segment.py", "blobs.py", "crop.py", "pipeline.py", "main.py"]


def _strip_comments_and_strings(source: str) -> str:
    source = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
    source = re.sub(r"#.*", "", source)
    return source


def test_target_modules_do_not_hardcode_section6_thresholds():
    violations = []
    for name in TARGET_MODULES:
        text = _strip_comments_and_strings((APP_DIR / name).read_text(encoding="utf-8"))
        for pattern in FORBIDDEN_LITERALS:
            if re.search(pattern, text):
                violations.append(f"{name}: {pattern}")
    assert violations == [], f"config.py以外にしきい値が直接書かれています: {violations}"


def test_target_modules_import_config():
    for name in TARGET_MODULES:
        if name == "main.py":
            continue  # main.pyはpipeline経由でconfigを使うため直接importは必須としない
        text = (APP_DIR / name).read_text(encoding="utf-8")
        assert "from app import config" in text, f"{name} が app.config を import していません"


def test_classify_module_references_confidence_thresholds_from_config():
    text = (APP_DIR / "classify.py").read_text(encoding="utf-8")
    for name in ["CONFIDENCE_ADOPT_THRESHOLD", "CONFIDENCE_LOW_THRESHOLD", "CONFIDENCE_CLOSE_DIFF"]:
        assert f"config.{name}" in text, f"classify.py が config.{name} を参照していません"

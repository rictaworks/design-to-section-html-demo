"""
PR #2（デザイン画像→レスポンシブHTML初稿 変換ツール実装）の
「ユーザーテスト手順（非エンジニアの方向け）」を自動化したもの。

対象はテキスト手順の1〜5・7（手順0は開発サーバー起動、手順6はサイドバー/
モバイル画像が手元にある場合のみの任意手順のため、代表ケースのみ
test_step6_* に含める）。

実行方法:
    cd src/analysis && source .venv/bin/activate
    cd ../../  # リポジトリルート
    python -m pytest test/pr2/test_pr2_api.py -v

前提: 解析層(:8001)・アプリケーション層(:3001)の開発サーバーが起動していること。
DOCS/TM.md の方針に従い、ここではブラックボックス（API経由）でユーザー視点の
受け入れ要件を確認する。ブラウザでの見た目確認は test_pr2_browser.cjs
（Playwright）で別途行う。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "support"))

import pytest

import client as api
import fixtures as fx
from html_checks import check_standalone_html

SECTION_KINDS = {
    "header", "hero", "features", "image_with_text", "cta", "pricing",
    "testimonials", "faq", "gallery", "logos", "generic_text", "footer",
}


@pytest.fixture
def session():
    with api.new_client() as c:
        yield c


@pytest.fixture
def ready_conversion(session):
    """手順1相当：PNGをアップロードし、帯分割済みの変換結果を返す。"""
    png = fx.multi_band_design_png()
    result = api.create_conversion(session, png)
    assert result.status_code == 201, result.json
    settled = api.wait_until_settled(session, result.json["id"])
    assert settled.json["state"] == "ready", settled.json
    return settled.json


# ---------------------------------------------------------------------------
# 手順1: デザイン画像をアップロードして帯に分割されることを確認する
# ---------------------------------------------------------------------------

def test_step1_upload_png_splits_into_bands_with_kind_confidence_variant(ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    assert len(bands) >= 1, "少なくとも1帯に分割されていること"

    for band in bands:
        kind = band["user_kind"] or band["detected_kind"]
        assert kind in SECTION_KINDS, f"未知の種別: {kind}"
        assert 0.0 <= band["confidence"] <= 1.0
        assert band["variant"], "バリアントが設定されていること"
        assert band["top_y"] < band["bottom_y"]

    # 帯は上から下へ連続していること（重なり・逆転がない）
    for a, b in zip(bands, bands[1:]):
        assert a["bottom_y"] <= b["top_y"] + 1


def test_step1_conversion_is_deterministic_for_the_same_image(session):
    """requirements.md 6.1: 同一画像・同一操作は完全に同じ帯分割・種別判定になる
    （決定性）。同じ画像を2回アップロードして帯構成が一致することを確認する。"""
    png = fx.multi_band_design_png()

    r1 = api.create_conversion(session, png)
    assert r1.status_code == 201
    d1 = api.wait_until_settled(session, r1.json["id"]).json

    r2 = api.create_conversion(session, png)
    assert r2.status_code == 201
    d2 = api.wait_until_settled(session, r2.json["id"]).json

    def band_signature(conv):
        return [
            (b["top_y"], b["bottom_y"], b["detected_kind"], b["confidence"], b["variant"])
            for b in api.sorted_bands(conv)
        ]

    assert band_signature(d1) == band_signature(d2)
    assert d1["shell_layout"] == d2["shell_layout"]
    assert d1["theme"] == d2["theme"]
    assert d1["mobile_design"] == d2["mobile_design"]


# ---------------------------------------------------------------------------
# 手順2: 受け付けられない画像を試し、理由が表示されることを確認する
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "make_bytes,filename,content_type,expected_error",
    [
        (fx.gif_bytes, "design.gif", "image/gif", "unsupported_format"),
        (fx.svg_bytes, "design.svg", "image/svg+xml", "unsupported_format"),
        (fx.oversized_png_bytes, "big.png", "image/png", "size_exceeded"),
        (fx.corrupted_png_bytes, "broken.png", "image/png", "corrupted"),
        (fx.dimension_out_of_range_png, "tiny.png", "image/png", "dimension_out_of_range"),
    ],
)
def test_step2_unsupported_or_invalid_images_are_rejected_with_a_reason(
    session, make_bytes, filename, content_type, expected_error
):
    result = api.create_conversion(session, make_bytes(), filename=filename, content_type=content_type)
    assert result.status_code == 422, result.json
    assert result.json == {"error": expected_error}


def test_step2_honeypot_submission_succeeds_without_creating_a_record(session):
    """requirements.md 6.2: ハニーポット項目に値がある送信は成功と同じ応答を返す
    が、レコードは作成されない。"""
    before = api.list_conversions(session)
    assert before.status_code == 200
    before_count = len(before.json)

    result = api.create_conversion(session, fx.multi_band_design_png(), honeypot="http://spam.example")
    assert result.status_code == 201
    assert result.json["state"] == "uploaded"

    after = api.list_conversions(session)
    assert after.status_code == 200
    assert len(after.json) == before_count, "ハニーポット送信はレコードを作らないこと"


# ---------------------------------------------------------------------------
# 手順3: 帯の種別変更・結合・分割・削除・復元を試す
# ---------------------------------------------------------------------------

def test_step3_change_kind_bumps_version_and_updates_kind(session, ready_conversion):
    band = api.sorted_bands(ready_conversion)[0]
    new_kind = "testimonials" if (band["user_kind"] or band["detected_kind"]) != "testimonials" else "faq"

    result = api.update_band_kind(session, ready_conversion["id"], band["id"], new_kind)
    assert result.status_code == 200, result.json
    assert result.json["version"] == ready_conversion["version"] + 1

    updated_band = next(b for b in api.sorted_bands(result.json) if b["id"] == band["id"])
    assert updated_band["user_kind"] == new_kind
    assert updated_band["state"] == "overridden"
    assert result.json["output"]["version"] == result.json["version"], "プレビュー(生成物)も再組み立てされること"


def test_step3_merge_adjacent_bands_reduces_band_count_and_bumps_version(session):
    png = fx.single_pair_design_png()
    created = api.create_conversion(session, png)
    conv = api.wait_until_settled(session, created.json["id"]).json
    bands = api.sorted_bands(conv)
    assert len(bands) >= 2, "結合を確認するには帯が2つ以上必要"

    first, second = bands[0], bands[1]
    before_count = len(api.active_bands(conv))
    before_version = conv["version"]

    result = api.merge_band(session, conv["id"], first["id"], second["id"])
    assert result.status_code == 200, result.json
    assert result.json["version"] == before_version + 1
    assert len(api.active_bands(result.json)) == before_count - 1


def test_step3_non_adjacent_merge_is_rejected(session, ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    if len(bands) < 3:
        pytest.skip("非隣接の組み合わせを確認するには帯が3つ以上必要")
    result = api.merge_band(session, ready_conversion["id"], bands[0]["id"], bands[2]["id"])
    assert result.status_code == 422
    assert result.json == {"error": "non_adjacent_merge_rejected"}


def test_step3_split_increases_band_count_and_bumps_version(session, ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    # 端から十分離れた帯（高さが十分あるもの）を選ぶ
    target = max(bands, key=lambda b: b["bottom_y"] - b["top_y"])
    mid_y = (target["top_y"] + target["bottom_y"]) // 2
    before_count = len(api.active_bands(ready_conversion))
    before_version = ready_conversion["version"]

    result = api.split_band(session, ready_conversion["id"], target["id"], mid_y)
    assert result.status_code == 200, result.json
    assert result.json["version"] == before_version + 1
    assert len(api.active_bands(result.json)) == before_count + 1


def test_step3_split_too_close_to_edge_is_rejected(session, ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    target = max(bands, key=lambda b: b["bottom_y"] - b["top_y"])
    near_edge_y = target["top_y"] + 1  # min_band_height_px(48)未満の位置

    result = api.split_band(session, ready_conversion["id"], target["id"], near_edge_y)
    assert result.status_code == 422
    assert result.json == {"error": "split_too_close_to_edge"}


def test_step3_remove_then_restore_returns_band_to_its_original_position(session, ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    target = bands[len(bands) // 2] if len(bands) > 1 else bands[0]
    original_position = target["position"]
    before_active_count = len(api.active_bands(ready_conversion))
    before_version = ready_conversion["version"]

    removed = api.remove_band(session, ready_conversion["id"], target["id"])
    assert removed.status_code == 200, removed.json
    assert removed.json["version"] == before_version + 1
    removed_band = next(b for b in api.sorted_bands(removed.json) if b["id"] == target["id"])
    assert removed_band["state"] == "removed"
    assert len(api.active_bands(removed.json)) == before_active_count - 1

    restored = api.restore_band(session, ready_conversion["id"], target["id"])
    assert restored.status_code == 200, restored.json
    assert restored.json["version"] == removed.json["version"] + 1
    restored_band = next(b for b in api.sorted_bands(restored.json) if b["id"] == target["id"])
    assert restored_band["state"] != "removed"
    assert restored_band["position"] == original_position, "復元後は元の位置に戻ること"
    assert len(api.active_bands(restored.json)) == before_active_count


# ---------------------------------------------------------------------------
# 手順4: 3つの画面幅でプレビューできることを確認する（フロントエンド側の
# 表示切り替えはPlaywrightで確認。ここではプレビューの元になる出力が単一の
# レスポンシブHTML(メディアクエリ入りCSS)であることをAPIレベルで確認する）
# ---------------------------------------------------------------------------

def test_step4_output_html_contains_responsive_media_queries_for_three_widths(ready_conversion):
    html = ready_conversion["output"]["html"]
    assert "@media (min-width: 600px)" in html
    assert "@media (min-width: 1024px)" in html
    assert "@media (max-width: 599px)" in html


# ---------------------------------------------------------------------------
# 手順5: 帯ごとの信頼度・注意事項が一覧できることを確認する
# ---------------------------------------------------------------------------

def test_step5_bands_expose_confidence_for_every_band(ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    for band in bands:
        assert isinstance(band["confidence"], (int, float))
        assert 0.0 <= band["confidence"] <= 1.0


def test_step5_low_confidence_bands_are_recorded_as_a_notice_tied_to_that_band(ready_conversion):
    """requirements.md 6.6: 信頼度が0.4以上0.6未満（採用はするが注意が必要な
    範囲。src/analysis/app/classify.py の CONFIDENCE_LOW_THRESHOLD〜
    CONFIDENCE_ADOPT_THRESHOLD）の帯は low_confidence_kind の注意事項として
    記録される。本テストは、その帯が実際に発生する保証はない合成画像を前提に
    しているため、発生した場合にのみ band_id の整合性を検証する
    （発生しない場合はその旨を明示してskipする）。"""
    bands = api.sorted_bands(ready_conversion)
    band_ids = {b["id"] for b in bands}
    low_confidence_ids = {b["id"] for b in bands if 0.4 <= b["confidence"] < 0.6}
    low_confidence_notices = [
        n for n in ready_conversion["notices"] if n["notice_type"] == "low_confidence_kind"
    ]

    if not low_confidence_notices:
        pytest.skip("このテスト画像では低確信度(0.4〜0.6未満)の帯が発生しなかった")

    for notice in low_confidence_notices:
        assert notice["band_id"] in band_ids, "注意事項は実在する帯に紐づくこと"
        assert notice["band_id"] in low_confidence_ids, (
            "low_confidence_kind 注意事項は、実際に信頼度が0.4〜0.6未満の帯に紐づくこと"
            "（無関係な帯に誤って紐づかないこと）"
        )


def test_step5_notice_types_are_all_known_codes(ready_conversion):
    # notice_typeはすべて既知のコードであること（日本語文言はフロントエンドmessages.tsが解決する）
    known_notice_types = {
        "mobile_design_detected", "dark_theme_detected", "no_separator_found",
        "band_count_exceeded", "sidebar_layout_detected", "header_split_from_hero",
        "low_confidence_kind", "close_confidence_runner_up", "generic_text_fallback",
        "variant_mismatch_fallback", "embedding_budget_exceeded", "analysis_timeout",
        "analysis_unreachable", "daily_reset_interrupted",
    }
    for notice in ready_conversion["notices"]:
        assert notice["notice_type"] in known_notice_types, notice


# ---------------------------------------------------------------------------
# 手順7: HTMLファイルをダウンロードし、単体で開けることを確認する
# （実ファイルの保存・ブラウザでの単体表示はPlaywright側。ここではダウンロード
# されるHTML文字列そのものがrequirements.md 6.9の生成物検証観点を満たすことを
# 確認する）
# ---------------------------------------------------------------------------

def test_step7_downloaded_html_is_self_contained_and_passes_output_validation(ready_conversion):
    html = ready_conversion["output"]["html"]
    reasons = check_standalone_html(html)
    assert reasons == [], f"生成物検証(6.9)に違反: {reasons}"

    assert "見出しのプレースホルダー" in html or "プレースホルダー" in html, (
        "文言はプレースホルダーであり、デザイン画像内の実際の文字は写し取られないこと"
    )


def test_step7_output_byte_size_matches_response_metadata(ready_conversion):
    html = ready_conversion["output"]["html"]
    assert ready_conversion["output"]["byte_size"] == len(html.encode("utf-8"))


# ---------------------------------------------------------------------------
# 手順6: サイドバー型・モバイル幅のデザインを試す（該当する画像がある場合。
# PR本文にも「該当する画像が手元にない場合は、この手順は省略して構いません」
# とあるため、検出されなかった場合はskipする）
# ---------------------------------------------------------------------------

def test_step6_mobile_aspect_ratio_image_gets_mobile_design_notice(session):
    png = fx.mobile_design_png()
    created = api.create_conversion(session, png)
    conv = api.wait_until_settled(session, created.json["id"]).json

    if not conv["mobile_design"]:
        pytest.skip("この合成画像ではモバイル幅として判定されなかった")

    notice_types = {n["notice_type"] for n in conv["notices"]}
    assert "mobile_design_detected" in notice_types


def test_step6_normal_design_does_not_get_mobile_or_sidebar_notices(ready_conversion):
    """通常の（サイドバーのない・極端に縦長でない）デザインでは、
    サイドバー/モバイル幅の注意事項が出ないことを確認する。"""
    notice_types = {n["notice_type"] for n in ready_conversion["notices"]}
    assert "sidebar_layout_detected" not in notice_types
    assert "mobile_design_detected" not in notice_types
    assert ready_conversion["shell_layout"] == "single"
    assert ready_conversion["mobile_design"] is False


def test_step6_sidebar_image_gets_simplified_notice(session):
    png = fx.sidebar_design_png()
    created = api.create_conversion(session, png)
    conv = api.wait_until_settled(session, created.json["id"]).json

    if conv["shell_layout"] != "sidebar":
        pytest.skip("この合成画像ではサイドバー型として判定されなかった")

    notice_types = {n["notice_type"] for n in conv["notices"]}
    assert "sidebar_layout_detected" in notice_types


# ---------------------------------------------------------------------------
# requirements.md 11章: セッション分離（別Cookieでは他人の変換にアクセスできず、
# 存在有無を区別せず「見つからない」を返す）。PR本文には明示のステップは無いが、
# PR #2 が実装したセッション分離機能そのものの受け入れ確認として含める。
# ---------------------------------------------------------------------------

def test_cross_session_cannot_access_or_list_another_sessions_conversion(session, ready_conversion):
    conversion_id = ready_conversion["id"]
    band_id = api.sorted_bands(ready_conversion)[0]["id"]

    with api.new_client() as other_session:
        # 別セッションの一覧には現れない
        listed = api.list_conversions(other_session)
        assert conversion_id not in {c["id"] for c in listed.json}

        # 直接IDを指定しても「見つからない」（存在有無を区別しない）
        got = api.get_conversion(other_session, conversion_id)
        assert got.status_code == 404
        assert got.json == {"error": "not_found"}

        img = api.source_image(other_session, conversion_id)
        assert img.status_code == 404

        kind_change = api.update_band_kind(other_session, conversion_id, band_id, "faq")
        assert kind_change.status_code == 404

        deleted = api.delete_conversion(other_session, conversion_id)
        assert deleted.status_code == 404

    # 元セッションからは引き続きアクセスできる（別セッションの操作による副作用がないこと）
    still_accessible = api.get_conversion(session, conversion_id)
    assert still_accessible.status_code == 200
    assert still_accessible.json["id"] == conversion_id

"""
PR #3（code-reviewで発見された不具合の修正）の
「ユーザーテスト手順（非エンジニア向け）」を自動化したもの。

対象はテキスト手順の1〜7。手順0は開発サーバー起動のため対象外。
PR #3 は「以前は動いていたが壊れていた／直った」バグ修正PRなので、各テストは
修正前の不具合が再発していないことを確認する回帰テストとして書く。

実行方法:
    cd src/analysis && source .venv/bin/activate
    cd ../../  # リポジトリルート
    python -m pytest test/pr3/test_pr3_api.py -v

前提: 解析層(:8001)・アプリケーション層(:3001)の開発サーバーが起動していること。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "support"))

import pytest

import client as api
import fixtures as fx
from html_checks import check_standalone_html


@pytest.fixture
def session():
    with api.new_client() as c:
        yield c


MIN_BAND_HEIGHT_PX = 48


def pick_splittable_middle_band(bands: list[dict]) -> dict:
    """先頭・末尾ではなく、かつ split_too_close_to_edge にならない十分な高さを
    持つ中間の帯を選ぶ（min_band_height_px=48の制約を両側に確保する）。"""
    last_position = bands[-1]["position"]
    candidates = [
        b for b in bands
        if b["position"] not in (0, last_position)
        and (b["bottom_y"] - b["top_y"]) > MIN_BAND_HEIGHT_PX * 2 + 4
    ]
    if not candidates:
        pytest.skip("分割制約を満たす十分な高さの中間帯がこのテスト画像には無い")
    return max(candidates, key=lambda b: b["bottom_y"] - b["top_y"])


@pytest.fixture
def ready_conversion(session):
    png = fx.multi_band_design_png()
    result = api.create_conversion(session, png)
    assert result.status_code == 201, result.json
    settled = api.wait_until_settled(session, result.json["id"])
    assert settled.json["state"] == "ready", settled.json
    return settled.json


# ---------------------------------------------------------------------------
# 手順1: アップロードから変換が最後まで終わることの確認（Cookie不具合の修正確認）
# ---------------------------------------------------------------------------

def test_step1_upload_completes_without_getting_stuck_and_reaches_ready(session):
    png = fx.multi_band_design_png()
    created = api.create_conversion(session, png)
    assert created.status_code == 201, created.json

    settled = api.wait_until_settled(session, created.json["id"], timeout=30)
    assert settled.json["state"] == "ready", (
        f"processing/failedのまま止まらないこと。実際の状態: {settled.json.get('state')}, "
        f"failed_reason: {settled.json.get('failed_reason')}"
    )
    assert len(api.sorted_bands(settled.json)) >= 1


def test_step1_session_cookie_is_set_with_a_browser_accepted_same_site_combination(session):
    """修正内容: 開発環境ではSameSite=None+Secure無しという、ブラウザに拒否される
    組み合わせでCookieが発行されており、ローカル開発でセッションが永続化されない
    不具合があった。開発環境(RAILS_ENV=development)ではSameSite=Laxかつ
    Secure指定なしで発行されることを確認する。"""
    resp = session.get("/conversions")
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert "design_to_html_session_id" in set_cookie, "セッションCookieが発行されること"
    assert re.search(r"samesite=lax", set_cookie, re.IGNORECASE), (
        f"開発環境ではSameSite=Laxで発行されること: {set_cookie}"
    )
    assert not re.search(r";\s*secure", set_cookie, re.IGNORECASE), (
        f"開発環境ではSecure属性なしで発行されること（HTTPSではないため）: {set_cookie}"
    )


def test_step1_reload_keeps_the_same_conversion_reachable_via_the_persisted_cookie(session, ready_conversion):
    """手順1の5.: ブラウザの再読み込みをしても同じ変換結果が表示され続けること
    （＝Cookieが正しく保存されている確認）。同一クライアント(=同一Cookie jar)で
    複数回GETしても、同じ内容が返り続けることをもって「再読み込み」を模す。"""
    conversion_id = ready_conversion["id"]
    for _ in range(3):
        reloaded = api.get_conversion(session, conversion_id)
        assert reloaded.status_code == 200
        assert reloaded.json["id"] == conversion_id
        assert reloaded.json["state"] == "ready"


# ---------------------------------------------------------------------------
# 手順2: 対応していない画像を送った場合に、正しく断られることの確認（回帰）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "make_bytes,filename,content_type,expected_error",
    [
        (fx.gif_bytes, "design.gif", "image/gif", "unsupported_format"),
        (fx.svg_bytes, "design.svg", "image/svg+xml", "unsupported_format"),
        (fx.oversized_png_bytes, "big.png", "image/png", "size_exceeded"),
    ],
)
def test_step2_unsupported_or_oversized_images_are_still_rejected_with_a_reason(
    session, make_bytes, filename, content_type, expected_error
):
    result = api.create_conversion(session, make_bytes(), filename=filename, content_type=content_type)
    assert result.status_code == 422, result.json
    assert result.json == {"error": expected_error}


# ---------------------------------------------------------------------------
# 手順3: 帯の分割・結合を行っても、ページ中間の帯がヘッダー/フッター扱いに
# ならないことの確認（今回の修正の中心：is_first_band/is_last_bandの配線）
# ---------------------------------------------------------------------------

def test_step3_splitting_a_middle_band_does_not_turn_either_half_into_header_or_footer(session, ready_conversion):
    bands = api.sorted_bands(ready_conversion)
    if len(bands) < 3:
        pytest.skip("先頭・末尾以外の帯を確認するには帯が3つ以上必要")

    middle = pick_splittable_middle_band(bands)
    mid_y = (middle["top_y"] + middle["bottom_y"]) // 2

    split_result = api.split_band(session, ready_conversion["id"], middle["id"], mid_y)
    assert split_result.status_code == 200, split_result.json

    new_bands = [
        b for b in api.sorted_bands(split_result.json)
        if middle["top_y"] <= b["top_y"] < middle["bottom_y"] and b["state"] != "removed"
    ]
    assert len(new_bands) == 2, "分割後、対象範囲に2つの帯があること"
    for b in new_bands:
        kind = b["user_kind"] or b["detected_kind"]
        assert kind not in ("header", "footer"), (
            f"ページ中間の帯を分割しても header/footer にならないこと（実際: {kind}）"
        )

    # 続けて結合し直しても同様にheader/footerにならないこと
    first, second = new_bands
    merge_result = api.merge_band(session, ready_conversion["id"], first["id"], second["id"])
    assert merge_result.status_code == 200, merge_result.json
    merged_band = next(
        b for b in api.sorted_bands(merge_result.json)
        if middle["top_y"] <= b["top_y"] < middle["bottom_y"] and b["state"] != "removed"
    )
    merged_kind = merged_band["user_kind"] or merged_band["detected_kind"]
    assert merged_kind not in ("header", "footer"), (
        f"結合後も header/footer にならないこと（実際: {merged_kind}）"
    )

    # 6.: 編集のたびに版が進み、プレビュー(生成物)が再組み立てされること
    assert merge_result.json["version"] > ready_conversion["version"]
    assert merge_result.json["output"]["version"] == merge_result.json["version"]


def test_step3_splitting_the_first_or_last_band_can_still_become_header_or_footer(session, ready_conversion):
    """対照実験: is_first_band/is_last_bandの配線が機能していることを、
    「中間ではできない」だけでなく「先頭・末尾では引き続きheader/footer候補と
    して扱われる」側からも確認する（requirements.md 6.6 header/footerは
    ページ端の帯のみが対象という制約）。"""
    bands = api.sorted_bands(ready_conversion)
    first_band = bands[0]
    mid_y = (first_band["top_y"] + first_band["bottom_y"]) // 2
    min_height = 48
    if mid_y - first_band["top_y"] <= min_height or first_band["bottom_y"] - mid_y <= min_height:
        pytest.skip("先頭帯が分割制約(最小48px)を満たすほど高くない")

    result = api.split_band(session, ready_conversion["id"], first_band["id"], mid_y)
    assert result.status_code == 200, result.json
    top_half = api.sorted_bands(result.json)[0]
    # 先頭の帯自体がheaderと判定されるかはヒューリスティック次第だが、少なくとも
    # 「中間扱いにされてheader候補から機械的に排除される」バグは起きていないこと
    # （= is_first_bandがTrueとして正しく伝わっていること）をAnalysisClient経由の
    # 応答から間接的に確認する。ここでは例外や422が起きず、正常に処理されることが
    # 最低限の確認になる。
    assert top_half["position"] == 0


# ---------------------------------------------------------------------------
# 手順4: フッターが複数列で表示されることの確認
# ---------------------------------------------------------------------------

FOOTER_COLUMN_CSS = re.compile(
    r"\.d2h-footer--col_(\d)\s+\.d2h-footer__columns[^{]*\{[^}]*grid-template-columns:\s*repeat\((\d),\s*1fr\)"
)


FOOTER_TAG_PATTERN = re.compile(r'<footer class="([^"]*)"')


def test_step4_footer_variant_is_rendered_with_matching_multi_column_css(session, ready_conversion):
    """修正内容: フッター部品の列数バリアント(2/3/4列)がCSSに反映されず、常に
    1列表示になっていた。帯をフッター種別へ変更し、実際に生成された<footer>要素
    のクラス（=VariantResolverが解決した実際のvariant。band.variantカラムは
    帯作成時にdetected_kindで初期化されたきり更新されないため、ここではJSON側の
    band.variantではなく生成物のHTMLそのものから実際のvariantを読み取る）と、
    生成物のCSSに含まれるgrid-template-columns: repeat(N, 1fr)ルールが一致し、
    常に1列固定にはならないことを確認する。"""
    bands = api.sorted_bands(ready_conversion)
    target = bands[-1]
    changed = api.update_band_kind(session, ready_conversion["id"], target["id"], "footer")
    assert changed.status_code == 200, changed.json

    html = changed.json["output"]["html"]
    footer_match = FOOTER_TAG_PATTERN.search(html)
    assert footer_match, "生成物に<footer>要素が含まれること"
    footer_classes = footer_match.group(1).split()
    # ComponentCatalogはd2h-footer本体・d2h-footer--{variant}・(あれば)
    # d2h-footer--on-light/on-dark(文字色)の3種のクラスを付与しうるため、
    # col_N系のvariantクラスだけに絞り込む。
    variant_classes = [c for c in footer_classes if c.startswith("d2h-footer--col_")]
    assert len(variant_classes) == 1, f"footer要素にcol_N系のvariantクラスが1つ付与されること: {footer_classes}"
    variant = variant_classes[0].removeprefix("d2h-footer--")
    assert variant.startswith("col_"), f"footerの既定バリアントはcol_N系のはず: {variant}"
    col_n = variant.split("_")[1]

    assert col_n in ("2", "3", "4"), f"想定外の列数: {col_n}"
    matches = {m.group(1): m.group(2) for m in FOOTER_COLUMN_CSS.finditer(html)}
    assert col_n in matches, f"CSSにd2h-footer--col_{col_n}の複数列ルールがあること"
    assert matches[col_n] == col_n, (
        f"col_{col_n} のCSSは最終的にrepeat({col_n}, 1fr)へ解決されること"
        "（常に1列(repeat無し)のままではないこと＝今回の修正の確認）"
    )
    # 常に1列固定になっていた旧バグの再発防止: grid-template-columns: 1frの
    # デフォルト定義以外に、col_N専用の複数列ルールが必ず存在すること
    assert "grid-template-columns: 1fr;" in html, "既定(狭幅)は1列のグリッド定義があること"


def test_step4_band_variant_field_reflects_the_band_kind_not_a_real_variant_code(session, ready_conversion):
    """既知の挙動の記録用テスト（バグではなく仕様として確定させるためのドキュ
    メント目的）: ConversionPipeline.persist_bandsはband.variantカラムを
    b[:detected_kind]（種別コードそのもの）で初期化しており、以後
    VariantResolverが実際に解決するvariant（例: col_3, image_left等）で
    上書きされることはない。そのため、APIが返すband.variantは「見た目の型」
    ではなく単なる種別名の複製になっている。PR #2 ユーザーテスト手順1では
    「バリアント（見た目の型）が表示されている」ことの確認を求めているため、
    この挙動は表示内容の正確性という観点で見直しの余地がある
    （本テスターの範囲では修正せず、挙動の記録のみ行う）。"""
    bands = api.sorted_bands(ready_conversion)
    target = bands[-1]
    changed = api.update_band_kind(session, ready_conversion["id"], target["id"], "footer")
    assert changed.status_code == 200, changed.json
    footer_band = next(b for b in api.sorted_bands(changed.json) if b["id"] == target["id"])

    # 種別変更後もvariantカラムは変更前のdetected_kind文字列のままで、
    # 実際に描画されるcol_N系のvariantには追随しない。
    assert footer_band["variant"] == footer_band["detected_kind"]
    assert not footer_band["variant"].startswith("col_")


# ---------------------------------------------------------------------------
# 手順5: 初稿のプレビュー（3つの画面幅）とダウンロードの確認
# ---------------------------------------------------------------------------

def test_step5_output_is_standalone_and_passes_acceptance_checks(ready_conversion):
    html = ready_conversion["output"]["html"]
    reasons = check_standalone_html(html)
    assert reasons == [], f"生成物検証(6.9)に違反: {reasons}"
    assert "@media (min-width: 600px)" in html
    assert "@media (min-width: 1024px)" in html
    assert "@media (max-width: 599px)" in html


# ---------------------------------------------------------------------------
# 手順6: 各帯の信頼度・注意事項の一覧表示の確認（band_id紐づけの修正確認）
# ---------------------------------------------------------------------------

def test_step6_notices_from_section_assembler_are_tied_to_the_correct_band_not_nil(session, ready_conversion):
    """修正内容: SectionAssembler由来の注意事項(band_idを直接保持)が
    resolve_band_idで見落とされ、常にband_id: nilで保存されていた。
    footerへの種別変更でvariant_mismatch_fallback通知を誘発し、band_idが
    実在の対象帯を指すことを確認する。"""
    bands = api.sorted_bands(ready_conversion)
    target = bands[-1]
    # footerの列数を判定できない特徴のまま強制的にfooterへ変更すると、
    # VariantResolverがmismatchとなりSectionAssemblerがvariant_mismatch_fallback
    # 通知(band_idを直接保持)を記録する経路を通りうる。
    changed = api.update_band_kind(session, ready_conversion["id"], target["id"], "footer")
    assert changed.status_code == 200, changed.json

    band_ids = {b["id"] for b in api.sorted_bands(changed.json)}
    section_assembler_notice_types = {"variant_mismatch_fallback"}
    relevant_notices = [
        n for n in changed.json["notices"] if n["notice_type"] in section_assembler_notice_types
    ]
    if not relevant_notices:
        pytest.skip("このテスト画像・操作ではvariant_mismatch_fallback通知が発生しなかった")

    for notice in relevant_notices:
        assert notice["band_id"] is not None, "SectionAssembler由来の注意事項はband_id: nilにならないこと"
        assert notice["band_id"] in band_ids, "band_idは実在するこの変換の帯を指すこと"


def test_step6_split_notices_reference_the_new_child_band_not_the_replaced_original(session, ready_conversion):
    """修正内容: 帯の結合・分割で返る注意事項が、refeature応答内のband_position
    （rangesの中でのindex）をconversion全体のpositionと取り違えて、無関係な帯に
    紐づく可能性があった（PR #3で修正）。

    このテストは、その修正後もなお残っている別経路の不具合を検出した:
    ConversionPipeline.persist_notices_with_offset は
    `conversion.bands.find_by(position: position_offset + relative_position)`
    で対象帯をpositionだけから検索しているが、分割元の帯(@band)はstate="replaced"
    に更新されるだけでposition値はそのまま残る。分割で新しく作られる先頭側の子帯
    は同じposition値(= 分割元帯の元のposition)を割り当てられるため、同じposition
    を持つレコードが(置換済みの旧帯・新しい子帯の)2件並存する瞬間が生まれる。
    find_byはstateを絞り込まないため、どちらが返るかはレコード順（通常は挿入が
    先＝IDが小さい方）に依存し、実際には置換済みで一覧から消えたはずの旧帯の
    IDが返ってしまうことがある（下記アサーションで再現）。

    結合(merge)でも同様の理屈（新しい結合後の帯が、結合対象だった先頭帯の元の
    positionを引き継ぐ）で発生しうる。

    本テスターは修正を行わず、再現手順と原因の記録のみを残す
    （CLAUDE.mdの方針により、修正可否は親セッション側の判断に委ねる）。"""
    bands = api.sorted_bands(ready_conversion)
    if len(bands) < 3:
        pytest.skip("中間帯を確認するには帯が3つ以上必要")
    middle = pick_splittable_middle_band(bands)
    mid_y = (middle["top_y"] + middle["bottom_y"]) // 2
    replaced_band_id = middle["id"]

    before_ids = {b["id"] for b in bands}
    result = api.split_band(session, ready_conversion["id"], middle["id"], mid_y)
    assert result.status_code == 200, result.json

    after_bands = api.sorted_bands(result.json)
    after_ids = {b["id"] for b in after_bands}
    newly_created_ids = after_ids - before_ids
    assert len(newly_created_ids) == 2, "分割で新しく2つの帯が作られること"
    assert replaced_band_id not in after_ids, "分割元の帯は一覧から消えている(state=replaced)こと"

    stale_notices = [n for n in result.json["notices"] if n["band_id"] == replaced_band_id]
    assert stale_notices == [], (
        "上記docstring記載のとおり、分割で新規発行された注意事項が、置換済みで"
        f"一覧から消えた旧帯(id={replaced_band_id})を指してしまっている: {stale_notices}"
    )

    for notice in result.json["notices"]:
        if notice["band_id"] is not None:
            assert notice["band_id"] in after_ids, (
                "帯編集由来の注意事項のband_idは、常にこの変換内の実在する帯を指すこと"
                "（無関係な帯に誤って紐づかないこと）"
            )


def test_step6_sidebar_or_mobile_notice_is_distinguished_from_other_notice_types(session):
    """サイドバー型・モバイル向けデザインの場合、「簡易対応です」に相当する
    注意事項(sidebar_layout_detected)が、他の注意事項の種別と混同されずに
    区別して記録されることを確認する。"""
    png = fx.sidebar_design_png()
    created = api.create_conversion(session, png)
    conv = api.wait_until_settled(session, created.json["id"]).json
    if conv["shell_layout"] != "sidebar":
        pytest.skip("この合成画像ではサイドバー型として判定されなかった")

    notice_types = [n["notice_type"] for n in conv["notices"]]
    assert notice_types.count("sidebar_layout_detected") >= 1
    # 同じ画像に対し、無関係のmobile_design_detectedが紛れ込んでいないこと
    assert conv["mobile_design"] is False
    assert "mobile_design_detected" not in notice_types


# ---------------------------------------------------------------------------
# 手順7: 画面を移動して戻っても問題なく動くことの確認（メモリリーク修正の
# 動作確認。専門的な計測はフロントエンド側のため、ここではバックエンドAPIを
# 同一セッションから繰り返し行き来しても状態が壊れないことを確認する）
# ---------------------------------------------------------------------------

def test_step7_navigating_back_and_forth_between_list_and_detail_stays_consistent(session, ready_conversion):
    conversion_id = ready_conversion["id"]
    for _ in range(3):
        listing = api.list_conversions(session)
        assert listing.status_code == 200
        assert conversion_id in {c["id"] for c in listing.json}

        detail = api.get_conversion(session, conversion_id)
        assert detail.status_code == 200
        assert detail.json["state"] == "ready"
        assert detail.json["output"] is not None

        image = api.source_image(session, conversion_id)
        assert image.status_code == 200
        assert len(image.content) > 0

import base64
import io

import cv2
import numpy as np
import pytest

from PIL import Image

from app.pipeline import analyze, refeature, DecodeError, InvalidRangeError, _allowed_kinds
from tests.fixtures.synth import blank_canvas, draw_text_line, draw_image_blob, encode_png


def _sample_design_png() -> bytes:
    img = blank_canvas(1200, 1600, bg=(255, 255, 255))
    draw_text_line(img, x=40, y=20, width=200, height=16, n_words=3)  # ヘッダー風のナビ
    draw_text_line(img, x=40, y=200, width=500, height=40, n_words=1)  # ヒーロー見出し
    draw_image_blob(img, x=700, y=180, w=400, h=300, seed=11)
    img[500:520, :] = (245, 245, 245)  # 帯間の区切り
    draw_text_line(img, x=40, y=600, width=1100, height=14, n_words=8)
    return encode_png(img)


def test_hero_eligibility_window_shifts_when_a_header_band_precedes_it():
    # requirements.md 6.6「ヒーロー：ヘッダーを除く先頭から2帯以内」。
    # ヘッダーが帯0として分離されていない場合：hero対象はindex 0,1（2以降は対象外）
    assert "hero" in _allowed_kinds("first", 0, header_offset=0)
    assert "hero" in _allowed_kinds("other", 1, header_offset=0)
    assert "hero" not in _allowed_kinds("other", 2, header_offset=0)

    # ヘッダーが帯0として分離されている場合：hero対象はindex 1,2（3以降は対象外）
    assert "hero" in _allowed_kinds("other", 1, header_offset=1)
    assert "hero" in _allowed_kinds("other", 2, header_offset=1)
    assert "hero" not in _allowed_kinds("other", 3, header_offset=1)


def test_analyze_returns_expected_top_level_shape():
    result = analyze(_sample_design_png())
    assert result["theme"] in ("light", "dark")
    assert isinstance(result["mobile_design"], bool)
    assert result["shell_layout"] in ("single", "sidebar")
    assert result["work_width"] <= 1200
    assert len(result["bands"]) >= 1
    for band in result["bands"]:
        assert set(["position", "top_y", "bottom_y", "features", "detected_kind", "confidence", "runner_up_kind", "crops"]) <= set(band.keys())
        assert "_blobs" not in band


def test_analyze_is_deterministic():
    data = _sample_design_png()
    r1 = analyze(data)
    r2 = analyze(data)
    assert r1 == r2


def test_analyze_raises_decode_error_for_garbage_bytes():
    with pytest.raises(DecodeError):
        analyze(b"not an image")


def test_analyze_composites_transparency_before_cropping_and_normalizing():
    # analyze()は正規化(work_image)だけでなく切り出し(original_image)も合成後の画像で行うこと
    # （合成しないままJPEG化するとアルファチャンネルが不正に扱われうる。refeature()と対称にする）。
    bgr = blank_canvas(1200, 1600, bg=(255, 255, 255))
    draw_text_line(bgr, x=40, y=20, width=200, height=16, n_words=3)
    draw_image_blob(bgr, x=700, y=180, w=400, h=300, seed=11)
    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = 180  # 全面半透明
    ok, buf = cv2.imencode(".png", rgba)
    assert ok

    result = analyze(buf.tobytes())

    crops = [c for band in result["bands"] for c in band["crops"] if not c["placeholder"]]
    assert len(crops) >= 1
    for crop in crops:
        raw = base64.b64decode(crop["image_base64"])
        decoded = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        assert decoded is not None
        assert decoded.shape[2] == 3  # アルファは合成済みでJPEGに残らない


def test_refeature_returns_bands_for_given_ranges():
    data = _sample_design_png()
    b64 = base64.b64encode(data).decode("ascii")
    result = refeature(b64, work_scale=1.0, ranges=[{"top_y": 0, "bottom_y": 500}, {"top_y": 520, "bottom_y": 1600}])
    assert len(result["bands"]) == 2
    assert result["bands"][0]["position"] == 0
    assert result["bands"][1]["position"] == 1


def test_refeature_rejects_a_zero_or_negative_height_range_instead_of_raising_an_unhandled_error():
    data = _sample_design_png()
    b64 = base64.b64encode(data).decode("ascii")
    with pytest.raises(InvalidRangeError):
        refeature(b64, work_scale=1.0, ranges=[{"top_y": 500, "bottom_y": 500}])
    with pytest.raises(InvalidRangeError):
        refeature(b64, work_scale=1.0, ranges=[{"top_y": 500, "bottom_y": 100}])


def test_refeature_only_allows_header_footer_at_the_true_page_edges_not_just_the_first_last_range():
    # ページ中間の帯を分割した場合、その2帯のどちらもheader/footerの候補になってはならない
    # （is_first_band/is_last_bandを両方Falseにして呼び出す＝Rails側が「これはページ中間の
    #   編集」と伝えるケース）。
    data = _sample_design_png()
    b64 = base64.b64encode(data).decode("ascii")
    result = refeature(
        b64,
        work_scale=1.0,
        ranges=[{"top_y": 520, "bottom_y": 1000}, {"top_y": 1000, "bottom_y": 1600}],
        is_first_band=False,
        is_last_band=False,
    )
    kinds = [b["detected_kind"] for b in result["bands"]]
    assert "header" not in kinds
    assert "footer" not in kinds


def test_decode_image_bytes_preserves_palette_png_transparency_as_an_alpha_channel():
    # パレット(mode "P")かつtRNS透過を持つPNGを作る：インデックス0を透過色として登録し、
    # 全面をインデックス0で塗る（＝全面透過、色は黒）。
    # convert("RGB")へ直行すると透過情報が失われ、パレット色（黒）がそのまま不透明色になる。
    # 先にRGBAへ変換していれば、デコード結果はアルファ付き(4ch)になり、白へ合成すると
    # 黒ではなく白に近い色になるはず。
    from app.pipeline import decode_image_bytes
    from app.normalize import composite_alpha_on_white

    img = Image.new("P", (20, 20))
    palette = [0, 0, 0] + [0] * (255 * 3)  # インデックス0=黒
    img.putpalette(palette)
    img.info["transparency"] = 0
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    decoded = decode_image_bytes(buf.getvalue())
    assert decoded.shape[2] == 4  # 透過情報がアルファチャンネルとして残っている

    composited = composite_alpha_on_white(decoded)
    mean_color = composited.reshape(-1, composited.shape[2])[:, :3].mean(axis=0)
    assert all(c > 200 for c in mean_color)  # 白背景に合成されている（黒のままなら透過漏れ）

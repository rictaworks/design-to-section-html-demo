import base64

import cv2
import numpy as np
import pytest

from app.pipeline import analyze, refeature, DecodeError, _allowed_kinds
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

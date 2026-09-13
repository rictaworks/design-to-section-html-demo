import base64

import pytest

from app.pipeline import analyze, refeature, DecodeError
from tests.fixtures.synth import blank_canvas, draw_text_line, draw_image_blob, encode_png


def _sample_design_png() -> bytes:
    img = blank_canvas(1200, 1600, bg=(255, 255, 255))
    draw_text_line(img, x=40, y=20, width=200, height=16, n_words=3)  # ヘッダー風のナビ
    draw_text_line(img, x=40, y=200, width=500, height=40, n_words=1)  # ヒーロー見出し
    draw_image_blob(img, x=700, y=180, w=400, h=300, seed=11)
    img[500:520, :] = (245, 245, 245)  # 帯間の区切り
    draw_text_line(img, x=40, y=600, width=1100, height=14, n_words=8)
    return encode_png(img)


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


def test_refeature_returns_bands_for_given_ranges():
    data = _sample_design_png()
    b64 = base64.b64encode(data).decode("ascii")
    result = refeature(b64, work_scale=1.0, ranges=[{"top_y": 0, "bottom_y": 500}, {"top_y": 520, "bottom_y": 1600}])
    assert len(result["bands"]) == 2
    assert result["bands"][0]["position"] == 0
    assert result["bands"][1]["position"] == 1

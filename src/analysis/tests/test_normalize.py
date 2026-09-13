import numpy as np

from app import config
from app.normalize import normalize_image
from tests.fixtures.synth import blank_canvas


def test_shrinks_when_wider_than_work_width_max():
    img = blank_canvas(2400, 1200)
    result = normalize_image(img)
    assert result.work_image.shape[1] == config.WORK_WIDTH_MAX
    assert result.work_scale == config.WORK_WIDTH_MAX / 2400


def test_does_not_enlarge_when_narrower_than_work_width_max():
    img = blank_canvas(800, 600)
    result = normalize_image(img)
    assert result.work_image.shape[1] == 800
    assert result.work_scale == 1.0


def test_detects_light_theme_from_border_pixels():
    img = blank_canvas(900, 900, bg=(255, 255, 255))
    result = normalize_image(img)
    assert result.theme == "light"


def test_detects_dark_theme_from_border_pixels():
    img = blank_canvas(900, 900, bg=(10, 10, 10))
    result = normalize_image(img)
    assert result.theme == "dark"
    assert "dark_theme_detected" in [n["notice_type"] for n in result.notices]


def test_flags_mobile_design_when_narrow_and_tall():
    img = blank_canvas(400, 1200, bg=(255, 255, 255))
    result = normalize_image(img)
    assert result.mobile_design is True
    assert "mobile_design_detected" in [n["notice_type"] for n in result.notices]


def test_does_not_flag_mobile_design_for_normal_ratio():
    img = blank_canvas(1200, 1600, bg=(255, 255, 255))
    result = normalize_image(img)
    assert result.mobile_design is False


def test_composites_transparency_onto_white():
    rgba = np.zeros((100, 100, 4), dtype=np.uint8)
    rgba[:, :, 3] = 0  # 全面透過
    result = normalize_image(rgba)
    # 透過は白へ合成されるため、作業画像の中心は白に近いはず
    center = result.work_image[50, 50]
    assert all(int(c) >= 250 for c in center)


def test_is_deterministic_for_same_input():
    img = blank_canvas(2000, 1000)
    r1 = normalize_image(img)
    r2 = normalize_image(img)
    assert np.array_equal(r1.work_image, r2.work_image)
    assert r1.theme == r2.theme
    assert r1.work_scale == r2.work_scale

import numpy as np

from app import config
from app.segment import (
    segment_bands,
    _enforce_min_height,
    _enforce_max_bands,
    _merge_candidates,
    _blank_run_candidates,
    _color_jump_candidates,
)
from tests.fixtures.synth import blank_canvas


def test_enforce_min_height_merges_band_shorter_than_48px():
    ranges = [(0, 100), (100, 147), (147, 300)]  # 2番目の帯は47px
    result = _enforce_min_height(ranges)
    assert (100, 147) not in result
    assert sum(b - t for t, b in result) == 300


def test_enforce_min_height_keeps_band_of_exactly_49px():
    ranges = [(0, 100), (100, 149), (149, 300)]
    result = _enforce_min_height(ranges)
    assert (100, 149) in result


def test_enforce_max_bands_merges_smallest_when_exceeding_40():
    ranges = [(i * 50, i * 50 + 50) for i in range(41)]
    result, exceeded = _enforce_max_bands(ranges)
    assert len(result) == config.MAX_BANDS
    assert exceeded is True


def test_enforce_max_bands_noop_when_within_limit():
    ranges = [(i * 50, i * 50 + 50) for i in range(10)]
    result, exceeded = _enforce_max_bands(ranges)
    assert result == ranges
    assert exceeded is False


def test_merge_candidates_drops_points_closer_than_min_gap():
    result = _merge_candidates([100, 103, 200], min_gap=48)
    assert result == [100, 200]


def test_blank_run_candidates_requires_minimum_run_length():
    ratio = np.array([0.5] * 10 + [0.0] * 5 + [0.5] * 10)  # 5px < 8px
    assert _blank_run_candidates(ratio) == []

    ratio2 = np.array([0.5] * 10 + [0.0] * 10 + [0.5] * 10)  # 10px >= 8px
    assert len(_blank_run_candidates(ratio2)) == 1


def test_color_jump_candidates_ignores_gradual_gradient():
    height = 60
    colors = np.zeros((height, 3))
    for y in range(height):
        colors[y] = [y * 2, y * 2, y * 2]  # 緩やかな連続変化
    assert _color_jump_candidates(colors) == []


def test_color_jump_candidates_detects_step_change():
    height = 60
    colors = np.zeros((height, 3))
    colors[:30] = [255, 255, 255]
    colors[30:] = [10, 10, 10]
    result = _color_jump_candidates(colors)
    assert 30 in result


def test_segment_whole_image_as_one_band_when_no_separator():
    img = blank_canvas(300, 300)
    result = segment_bands(img, bg_color=(255, 255, 255))
    assert result.band_ranges == [(0, 300)]
    assert any(n["notice_type"] == config.NOTICE_NO_SEPARATOR_FOUND for n in result.notices)


def test_segment_splits_on_blank_gap_between_content_blocks():
    img = blank_canvas(200, 400, bg=(255, 255, 255))
    img[20:80, 20:180] = (10, 10, 10)
    img[220:280, 20:180] = (10, 10, 10)
    result = segment_bands(img, bg_color=(255, 255, 255))
    assert len(result.band_ranges) >= 2


def test_segment_detects_sidebar_when_tall_narrow_vertical_edge_present():
    img = blank_canvas(600, 500, bg=(255, 255, 255))
    img[:, 0:150] = (200, 200, 200)  # サイドバー領域（幅30%未満・高さ全体）
    result = segment_bands(img, bg_color=(255, 255, 255))
    assert result.shell_layout == "sidebar"
    assert any(n["notice_type"] == config.NOTICE_SIDEBAR_LAYOUT_DETECTED for n in result.notices)


def test_segment_is_deterministic():
    img = blank_canvas(300, 400, bg=(255, 255, 255))
    img[50:100, 20:200] = (10, 10, 10)
    r1 = segment_bands(img, bg_color=(255, 255, 255))
    r2 = segment_bands(img, bg_color=(255, 255, 255))
    assert r1.band_ranges == r2.band_ranges

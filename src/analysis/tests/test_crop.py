import base64
from types import SimpleNamespace

from app import config
from app.crop import crop_blob, EmbedBudget
from tests.fixtures.synth import blank_canvas, draw_image_blob


def make_blob(x, y, w, h, kind="image"):
    return SimpleNamespace(x=x, y=y, w=w, h=h, kind=kind)


def test_crop_shrinks_long_edge_to_800px_max():
    original = blank_canvas(2000, 2000)
    draw_image_blob(original, x=100, y=100, w=1600, h=1200, seed=9)
    blob = make_blob(x=100, y=100, w=1600, h=1200)
    budget = EmbedBudget()
    result = crop_blob(original, work_scale=1.0, band_top_work=0, blob=blob, budget=budget)
    assert result["placeholder"] is False
    raw = base64.b64decode(result["image_base64"])
    import cv2
    import numpy as np

    decoded = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    assert max(decoded.shape[:2]) <= config.CROP_LONG_EDGE_PX


def test_crop_maps_work_coordinates_back_to_original_using_work_scale():
    original = blank_canvas(4000, 3000)
    draw_image_blob(original, x=400, y=200, w=800, h=600, seed=1)
    work_scale = 1200 / 4000  # 0.3
    blob = make_blob(x=int(400 * work_scale), y=int(200 * work_scale), w=int(800 * work_scale), h=int(600 * work_scale))
    budget = EmbedBudget()
    result = crop_blob(original, work_scale=work_scale, band_top_work=0, blob=blob, budget=budget)
    assert abs(result["left_x"] - 400) <= 4
    assert abs(result["top_y"] - 200) <= 4
    assert abs(result["width"] - 800) <= 4
    assert abs(result["height"] - 600) <= 4


def test_crop_becomes_placeholder_when_budget_exhausted():
    original = blank_canvas(2000, 2000)
    draw_image_blob(original, x=0, y=0, w=1000, h=1000, seed=3)
    blob = make_blob(x=0, y=0, w=1000, h=1000)
    budget = EmbedBudget(limit_bytes=0)  # 予算ゼロ＝必ず超過
    result = crop_blob(original, work_scale=1.0, band_top_work=0, blob=blob, budget=budget)
    assert result["placeholder"] is True
    assert result["image_base64"] == ""


def test_crop_shape_is_circle_for_circle_image_blob():
    original = blank_canvas(400, 400)
    draw_image_blob(original, x=100, y=100, w=200, h=200, seed=7)
    blob = make_blob(x=100, y=100, w=200, h=200, kind="circle_image")
    result = crop_blob(original, work_scale=1.0, band_top_work=0, blob=blob, budget=EmbedBudget())
    assert result["shape"] == "circle"


def test_budget_is_measured_on_the_base64_encoded_size_actually_embedded_in_html():
    # 予算はHTMLへ埋め込まれるサイズ（base64文字列長）を基準にすること。
    # base64化前の生JPEGバイト数で計測すると、実際の埋め込みサイズを約4/3倍過小評価してしまう。
    original = blank_canvas(1000, 1000)
    draw_image_blob(original, x=0, y=0, w=500, h=500, seed=5)
    blob = make_blob(x=0, y=0, w=500, h=500)
    budget = EmbedBudget()
    result = crop_blob(original, work_scale=1.0, band_top_work=0, blob=blob, budget=budget)
    assert result["placeholder"] is False
    assert budget.used_bytes == len(result["image_base64"])


def test_budget_tracks_cumulative_usage_across_calls():
    original = blank_canvas(1000, 1000)
    draw_image_blob(original, x=0, y=0, w=500, h=500, seed=4)
    blob = make_blob(x=0, y=0, w=500, h=500)
    budget = EmbedBudget()
    r1 = crop_blob(original, 1.0, 0, blob, budget)
    used_after_first = budget.used_bytes
    assert used_after_first > 0
    r2 = crop_blob(original, 1.0, 0, blob, budget)
    assert budget.used_bytes >= used_after_first

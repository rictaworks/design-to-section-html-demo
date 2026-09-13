from app.features import extract_band_features
from tests.fixtures.synth import (
    blank_canvas,
    draw_text_line,
    draw_icon_blob,
    draw_image_blob,
    draw_button_blob,
)


def test_counts_text_blobs_and_computes_heading_scale():
    img = blank_canvas(800, 300, bg=(255, 255, 255))
    draw_text_line(img, x=20, y=30, width=300, height=24, n_words=1)  # 見出し相当
    draw_text_line(img, x=20, y=150, width=300, height=12, n_words=6)
    features, blobs = extract_band_features(
        img, position="other", work_width=1200, work_height=2000, band_top=0, band_bottom=300
    )
    assert features["text_blob_count"] >= 2
    assert features["max_text_blob_height"] >= 20
    assert features["heading_scale"] > 1.0


def test_column_count_from_horizontally_separated_icon_groups():
    img = blank_canvas(900, 300, bg=(255, 255, 255))
    for col_x in (50, 350, 650):
        draw_icon_blob(img, x=col_x, y=40, size=24)
        draw_text_line(img, x=col_x, y=100, width=150, n_words=3)
    features, _ = extract_band_features(
        img, position="other", work_width=1200, work_height=2000, band_top=0, band_bottom=300
    )
    assert features["column_count"] == 3
    assert features["repeat_count"] >= 3
    assert features["icon_blob_count"] == 3


def test_image_position_left_when_image_on_left_half():
    img = blank_canvas(800, 300, bg=(255, 255, 255))
    draw_image_blob(img, x=20, y=20, w=300, h=260, seed=3)
    draw_text_line(img, x=380, y=100, width=350, n_words=5)
    features, _ = extract_band_features(
        img, position="other", work_width=1200, work_height=2000, band_top=0, band_bottom=300
    )
    assert features["image_position"] == "left"


def test_image_position_none_when_no_image_blob():
    img = blank_canvas(800, 200, bg=(255, 255, 255))
    draw_text_line(img, x=50, y=90, width=400, n_words=6)
    features, _ = extract_band_features(
        img, position="other", work_width=1200, work_height=2000, band_top=0, band_bottom=200
    )
    assert features["image_position"] == "none"


def test_accent_color_from_button_blob():
    img = blank_canvas(800, 200, bg=(255, 255, 255))
    draw_button_blob(img, x=300, y=80, w=120, h=40, fill=(220, 100, 30))
    features, _ = extract_band_features(
        img, position="other", work_width=1200, work_height=2000, band_top=0, band_bottom=200
    )
    assert features["accent_color_hex"] is not None


def test_height_ratio_and_position_are_passed_through():
    img = blank_canvas(800, 100, bg=(255, 255, 255))
    features, _ = extract_band_features(
        img, position="first", work_width=1200, work_height=2000, band_top=0, band_bottom=100
    )
    assert features["height_ratio"] == 100 / 2000
    assert features["position"] == "first"

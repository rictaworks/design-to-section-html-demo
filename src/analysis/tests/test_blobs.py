from app.blobs import extract_and_classify
from tests.fixtures.synth import (
    blank_canvas,
    draw_text_line,
    draw_image_blob,
    draw_circle_image_blob,
    draw_button_blob,
    draw_icon_blob,
)


def test_classifies_text_line_words_as_text():
    img = blank_canvas(600, 120)
    draw_text_line(img, x=20, y=50, width=400, height=14, n_words=4)
    blobs = extract_and_classify(img)
    kinds = [b.kind for b in blobs]
    assert kinds.count("text") == 4


def test_classifies_large_high_variance_blob_as_image():
    img = blank_canvas(600, 400)
    draw_image_blob(img, x=50, y=50, w=300, h=250, seed=1)
    blobs = extract_and_classify(img)
    assert any(b.kind == "image" for b in blobs)


def test_classifies_circular_high_variance_blob_as_circle_image():
    img = blank_canvas(400, 400)
    draw_circle_image_blob(img, cx=200, cy=200, r=100, seed=2)
    blobs = extract_and_classify(img)
    assert any(b.kind == "circle_image" for b in blobs)


def test_classifies_solid_contrasting_midsize_rect_as_button():
    img = blank_canvas(600, 200, bg=(255, 255, 255))
    draw_button_blob(img, x=250, y=80, w=120, h=40, fill=(220, 100, 30), text_color=(255, 255, 255))
    blobs = extract_and_classify(img)
    assert any(b.kind == "button" for b in blobs)


def test_classifies_a_button_sized_blob_as_button_even_when_it_also_fits_the_text_height_threshold():
    # 帯が大きい（例：ヒーロー帯・CTA帯）と text_max_height が上限40pxまで緩むため、
    # 典型的なボタン（高さ30px程度）が文字状として誤判定されないことを確認する。
    img = blank_canvas(600, 400, bg=(255, 255, 255))
    draw_button_blob(img, x=250, y=180, w=120, h=30, fill=(220, 100, 30), text_color=(255, 255, 255))
    blobs = extract_and_classify(img)
    kinds = [b.kind for b in blobs]
    assert "button" in kinds
    assert "text" not in kinds


def test_classifies_small_low_variance_square_as_icon():
    img = blank_canvas(400, 200, bg=(255, 255, 255))
    draw_icon_blob(img, x=180, y=80, size=24, color=(90, 90, 90))
    blobs = extract_and_classify(img)
    assert any(b.kind == "icon" for b in blobs)


def test_is_deterministic():
    img = blank_canvas(600, 300)
    draw_image_blob(img, x=50, y=50, w=200, h=150, seed=5)
    draw_text_line(img, x=300, y=60, width=200, n_words=3)
    b1 = extract_and_classify(img)
    b2 = extract_and_classify(img)
    assert [(b.x, b.y, b.w, b.h, b.kind) for b in b1] == [(b.x, b.y, b.w, b.h, b.kind) for b in b2]

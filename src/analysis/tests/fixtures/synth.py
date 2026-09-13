"""テスト用の合成デザイン画像を決定的に生成するヘルパー。"""
import numpy as np
import cv2


def blank_canvas(width: int, height: int, bg=(255, 255, 255)):
    img = np.full((height, width, 3), bg, dtype=np.uint8)
    return img


def draw_text_blob(img, x, y, w, h, color=(20, 20, 20)):
    """横長矩形＝文字状ブロブの代用（塗りつぶし矩形の集合で「基準線が揃う」性質を模す）。"""
    cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness=-1)


def draw_text_line(img, x, y, width, height=14, color=(20, 20, 20), n_words=4):
    """基準線の揃った複数の短い矩形を横に並べ、1行の文字列を模す。"""
    word_w = max(4, width // (n_words * 2))
    gap = word_w
    cx = x
    for _ in range(n_words):
        draw_text_blob(img, cx, y, word_w, height, color)
        cx += word_w + gap


def draw_image_blob(img, x, y, w, h, seed=0):
    """内部の色分散が大きい矩形＝画像状ブロブの代用。"""
    rng = np.random.RandomState(seed)
    patch = rng.randint(0, 255, size=(h, w, 3), dtype=np.uint8)
    img[y : y + h, x : x + w] = patch


def draw_circle_image_blob(img, cx, cy, r, seed=0):
    rng = np.random.RandomState(seed)
    mask = np.zeros((r * 2, r * 2, 3), dtype=np.uint8)
    patch = rng.randint(0, 255, size=(r * 2, r * 2, 3), dtype=np.uint8)
    cv2.circle(mask, (r, r), r, (255, 255, 255), thickness=-1)
    region = img[cy - r : cy + r, cx - r : cx + r]
    region[mask[:, :, 0] > 0] = patch[mask[:, :, 0] > 0]


def draw_button_blob(img, x, y, w, h, fill=(30, 100, 220), text_color=(255, 255, 255)):
    cv2.rectangle(img, (x, y), (x + w, y + h), fill, thickness=-1)
    tw, th = int(w * 0.5), max(6, h // 3)
    tx, ty = x + (w - tw) // 2, y + (h - th) // 2
    cv2.rectangle(img, (tx, ty), (tx + tw, ty + th), text_color, thickness=-1)


def draw_icon_blob(img, x, y, size, color=(80, 80, 80)):
    cv2.rectangle(img, (x, y), (x + size, y + size), color, thickness=-1)


def encode_png(img) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


def encode_jpeg(img) -> bytes:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()

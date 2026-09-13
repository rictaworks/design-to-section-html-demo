"""
テスト用の合成デザイン画像を決定的に生成するヘルパー。

src/analysis/tests/fixtures/synth.py と同じ考え方（塗りつぶし矩形の集合で
文字列・画像領域・区切りを表現する）を踏襲しつつ、PR #2 / PR #3 のユーザー
テスト手順で必要な「複数の帯に分かれる1ページ分のデザイン画像」を生成する。

このファイルは src/analysis の実装（app.pipeline 等）を一切importしない
（テストハーネスが実装内部に依存して壊れやすくなるのを避けるため。DOCS/DP.md
のKISS/YAGNIに沿い、必要な部分だけをここに複製する）。
実行には numpy・opencv-python-headless が必要（src/analysis/.venv に導入済み）。
"""
from __future__ import annotations

import numpy as np
import cv2


def blank_canvas(width: int, height: int, bg=(255, 255, 255)):
    return np.full((height, width, 3), bg, dtype=np.uint8)


def draw_text_blob(img, x, y, w, h, color=(20, 20, 20)):
    cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness=-1)


def draw_text_line(img, x, y, width, height=14, color=(20, 20, 20), n_words=4):
    word_w = max(4, width // (n_words * 2))
    gap = word_w
    cx = x
    for _ in range(n_words):
        draw_text_blob(img, cx, y, word_w, height, color)
        cx += word_w + gap


def draw_image_blob(img, x, y, w, h, seed=0):
    rng = np.random.RandomState(seed)
    patch = rng.randint(0, 255, size=(h, w, 3), dtype=np.uint8)
    img[y : y + h, x : x + w] = patch


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


SEPARATOR_COLOR = (245, 245, 245)


def multi_band_design_png(width: int = 1600) -> bytes:
    """header / hero / features風 / pricing風 / footer風の5領域が、はっきりした
    区切り（帯間の余白）で分かれた1ページ分のデザイン画像（requirements.md 6.4の
    帯分割・PR本文の「縦に長い、いわゆる1枚のホームページ画像」を模す）。

    実際の種別判定（header/hero/features等になるか）は解析層の規則次第であり、
    このヘルパーは「複数の帯に分かれること」と「先頭でも末尾でもない帯が存在す
    ること」だけを保証する。
    """
    img = blank_canvas(width, 2200, bg=(255, 255, 255))

    # header風: 左にロゴ、右にナビ項目
    draw_text_line(img, x=40, y=50, width=160, height=20, n_words=1)
    draw_text_line(img, x=width - 400, y=55, width=360, height=14, n_words=4)
    img[140:160, :] = SEPARATOR_COLOR

    # hero風: 大見出し + 右側に画像
    draw_text_line(img, x=60, y=220, width=520, height=48, n_words=1)
    draw_text_line(img, x=60, y=300, width=600, height=16, n_words=10)
    draw_button_blob(img, x=60, y=360, w=160, h=48)
    draw_image_blob(img, x=width - 480, y=200, w=400, h=300, seed=11)
    img[560:580, :] = SEPARATOR_COLOR

    # features風: アイコン+短文を横に3つ並べる（列を持つ帯の代用）
    col_w = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (col_w + 40)
        draw_icon_blob(img, cx, 640, 56, color=(90, 90, 90))
        draw_text_line(img, cx, 720, width=col_w - 20, height=14, n_words=3)
        draw_text_line(img, cx, 750, width=col_w - 20, height=12, n_words=6)
    img[860:880, :] = SEPARATOR_COLOR

    # pricing風: ボタンを含む矩形カードを3つ
    card_w = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (card_w + 40)
        draw_text_blob(img, cx, 920, card_w - 20, 200, color=(250, 250, 250))
        draw_text_line(img, cx + 20, 950, width=card_w - 60, height=20, n_words=2)
        draw_button_blob(img, cx + 20, 1050, w=card_w - 60, h=40)
    img[1160:1180, :] = SEPARATOR_COLOR

    # generic text風（中間の帯、分割対象に使う）
    for i in range(6):
        draw_text_line(img, x=60, y=1220 + i * 30, width=width - 120, height=14, n_words=9)
    img[1420:1440, :] = SEPARATOR_COLOR

    # footer風: 3列のリンク一覧 + コピーライト
    fcol_w = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (fcol_w + 40)
        draw_text_line(img, cx, 1480, width=fcol_w - 20, height=16, n_words=2)
        for j in range(3):
            draw_text_line(img, cx, 1520 + j * 26, width=fcol_w - 40, height=12, n_words=2)
    draw_text_line(img, x=width // 2 - 150, y=1660, width=300, height=12, n_words=4)

    return encode_png(img)


def single_pair_design_png(width: int = 1200) -> bytes:
    """区切り1本のみを含む、帯2つのシンプルな画像（結合・分割の最小ケース用）。"""
    img = blank_canvas(width, 900, bg=(255, 255, 255))
    draw_text_line(img, x=40, y=40, width=300, height=24, n_words=2)
    draw_image_blob(img, x=width - 500, y=30, w=420, h=260, seed=3)
    img[430:450, :] = SEPARATOR_COLOR
    for i in range(6):
        draw_text_line(img, x=40, y=500 + i * 30, width=width - 80, height=14, n_words=9)
    return encode_png(img)


def gif_bytes() -> bytes:
    """PNG/JPEG/WebP以外の形式（GIF）。署名検査のみで拒否される想定なので、
    フルスペックのGIFファイルである必要はない。"""
    return b"GIF89a" + b"\x00" * 64


def svg_bytes() -> bytes:
    return b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'


def oversized_png_bytes(min_bytes: int = 10 * 1024 * 1024 + 1024) -> bytes:
    """10MB超の「大きすぎる」ファイル。サイズ検査はフォーマット判定より先に走る
    （IntakeValidator#validate）ため、末尾に無害なパディングを足すだけで良い。"""
    base = encode_png(blank_canvas(64, 64))
    padding = b"\x00" * (min_bytes - len(base))
    return base + padding


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def corrupted_png_bytes() -> bytes:
    """PNG署名はあるが、IHDRチャンク（幅・高さを含む先頭チャンク、シグネチャ8byte
    +長さ4byte+"IHDR"4byte+データ13byte+CRC4byte=33byte）を完全に含まない
    切り詰められたファイル。FastImage.sizeが寸法を取得できず nil を返すため、
    IntakeValidatorはcorruptedとして拒否する。"""
    real_png = encode_png(blank_canvas(400, 400))
    assert real_png.startswith(PNG_SIGNATURE)
    return real_png[:16]  # シグネチャ8byte + IHDRチャンクの途中まで


def dimension_out_of_range_png() -> bytes:
    """短辺がMIN_SHORT_EDGE(320px)未満の、寸法が小さすぎる正当なPNG。"""
    return encode_png(blank_canvas(200, 200))


def mobile_design_png(width: int = 400, height: int = 1400) -> bytes:
    """width < height * MOBILE_ASPECT_RATIO_THRESHOLD(0.7) となる縦長画像
    （src/analysis/app/normalize.py の mobile_design 判定を狙う）。
    PR #2 手順6「横幅に対して縦にとても長い画像」に相当する。"""
    img = blank_canvas(width, height, bg=(255, 255, 255))
    draw_text_line(img, x=20, y=20, width=width - 40, height=16, n_words=2)
    img[100:116, :] = SEPARATOR_COLOR
    draw_text_line(img, x=20, y=160, width=width - 40, height=28, n_words=1)
    draw_image_blob(img, x=20, y=220, w=width - 40, h=260, seed=5)
    img[520:536, :] = SEPARATOR_COLOR
    for i in range(10):
        draw_text_line(img, x=20, y=560 + i * 30, width=width - 40, height=12, n_words=6)
    return encode_png(img)


def sidebar_design_png(width: int = 1200, height: int = 1600) -> bytes:
    """左端(全体の30%未満)に、ほぼ全高にわたる強い縦の色境界を持つ画像
    （src/analysis/app/segment.py の _detect_sidebar を狙う。SIDEBAR_WIDTH_RATIO=0.3・
    SIDEBAR_HEIGHT_RATIO=0.8 に基づき、幅の20%・高さの90%にわたる塗りつぶし帯を
    左端に置く）。PR #2 手順6「左右どちらかに縦長のメニューがあるデザイン」に相当する。"""
    img = blank_canvas(width, height, bg=(255, 255, 255))
    sidebar_w = int(width * 0.2)
    cv2.rectangle(img, (0, 0), (sidebar_w, int(height * 0.95)), (60, 60, 60), thickness=-1)
    for i in range(8):
        draw_text_line(img, x=20, y=40 + i * 60, width=sidebar_w - 40, height=14, n_words=2, color=(230, 230, 230))

    content_x = sidebar_w + 40
    draw_text_line(img, x=content_x, y=60, width=width - content_x - 40, height=32, n_words=3)
    draw_image_blob(img, x=content_x, y=140, w=width - content_x - 40, h=260, seed=7)
    img[440:456, content_x:] = SEPARATOR_COLOR
    for i in range(8):
        draw_text_line(img, x=content_x, y=480 + i * 30, width=width - content_x - 40, height=12, n_words=8)
    return encode_png(img)

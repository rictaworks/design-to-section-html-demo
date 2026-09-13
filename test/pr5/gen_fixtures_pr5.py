"""
PR #5（マージ済み・01.01.03）の表示系修正を実サーバー・実ブラウザで最終確認するための
合成デザイン画像を生成するCLI。

test/support/fixtures.py の考え方（決定的な合成画像・src/analysisの実装をimportしない）を
踏襲しつつ、そこには無い「円形ブロブ（証言セクションの丸い顔写真を模す）」を追加する。
円は cv2.circle でマスクを作り、内部をランダムノイズで塗ることで
src/analysis/app/blobs.py の classify_blob が image/circle_image と判定する条件
（面積比・色分散・真円度）を満たす。

使い方:
    python3 gen_fixtures_pr5.py <出力ディレクトリ>

出力:
    <dir>/testimonials_page.png - header/hero/testimonials/cta/features/footerの
                                    6帯を含む1ページ分のデザイン画像
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "support"))
import fixtures as fx  # noqa: E402


def draw_circle_image_blob(img, cx: int, cy: int, radius: int, seed: int = 0):
    """円形の「顔写真」ブロブ。ノイズ塗りつぶしで色分散を確保し、
    真円マスクでcircularity>=CIRCLE_MIN_CIRCULARITY(0.85)を満たす。"""
    rng = np.random.RandomState(seed)
    y0, y1 = cy - radius, cy + radius
    x0, x1 = cx - radius, cx + radius
    size = y1 - y0
    patch = rng.randint(0, 255, size=(size, size, 3), dtype=np.uint8)
    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.circle(mask, (radius, radius), radius, 255, -1)
    region = img[y0:y1, x0:x1]
    region[mask == 255] = patch[mask == 255]


def testimonials_page_png(width: int = 1600) -> bytes:
    """header / hero / testimonials(円形3つ) / cta(中央寄せ) / features / footer の
    6帯を、はっきりした区切りで持つ1ページ分のデザイン画像。

    PR #5で修正された表示項目を1枚でまとめて確認できるように設計している:
      - testimonials帯: 証言の円形切り出し画像が壊れずに表示されるか
      - cta帯: ダーク/ライト配色でコントラストが保たれるか（帯の種別変更で両方試す）
      - footer帯: 列レイアウトが画面中央に適切な余白を持つか
    """
    img = fx.blank_canvas(width, 2000, bg=(255, 255, 255))

    # header (position=first)
    fx.draw_text_line(img, x=40, y=50, width=160, height=20, n_words=1)
    fx.draw_text_line(img, x=width - 400, y=55, width=360, height=14, n_words=4)
    img[140:160, :] = fx.SEPARATOR_COLOR

    # hero
    fx.draw_text_line(img, x=60, y=220, width=520, height=48, n_words=1)
    fx.draw_text_line(img, x=60, y=300, width=600, height=16, n_words=10)
    fx.draw_button_blob(img, x=60, y=360, w=160, h=48)
    fx.draw_image_blob(img, x=width - 480, y=200, w=400, h=300, seed=11)
    img[560:580, :] = fx.SEPARATOR_COLOR

    # testimonials: 3つの円形「顔写真」+ 各々の下に引用文
    radius = 70
    col_w = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (col_w + 40) + col_w // 2
        cy = 660 + radius
        draw_circle_image_blob(img, cx, cy, radius, seed=100 + i)
        fx.draw_text_line(img, x=80 + i * (col_w + 40), y=cy + radius + 30, width=col_w - 20, height=14, n_words=6)
        fx.draw_text_line(img, x=80 + i * (col_w + 40), y=cy + radius + 60, width=col_w - 40, height=12, n_words=3)
    img[980:1000, :] = fx.SEPARATOR_COLOR

    # cta(light): 中央寄せの見出し+サブテキスト+ボタン1つ（背景は白＝bg_luminance高）
    fx.draw_text_line(img, x=width // 2 - 220, y=1040, width=440, height=32, n_words=1)
    fx.draw_text_line(img, x=width // 2 - 180, y=1090, width=360, height=14, n_words=6)
    fx.draw_button_blob(img, x=width // 2 - 90, y=1120, w=180, h=44)
    img[1170:1190, :] = fx.SEPARATOR_COLOR

    # cta(dark): 同じ構図だが帯全体を暗い背景で塗り、text_color=light(=on-dark配色)を狙う
    # (src/backend/app/services/parameter_extractor.rb の text_color: bg_luminance<0.5でlight)。
    # 前景要素はFOREGROUND_COLOR_DIST_THRESHOLD(24)を超える明るい色にし、ボタンは
    # BUTTON_MAX_COLOR_STD(20)以下・contrast>=40を満たす単色にする。
    img[1190:1370, :] = (20, 20, 20)
    fx.draw_text_line(img, x=width // 2 - 220, y=1230, width=440, height=32, n_words=1, color=(235, 235, 235))
    fx.draw_text_line(img, x=width // 2 - 180, y=1280, width=360, height=14, n_words=6, color=(200, 200, 200))
    fx.draw_button_blob(img, x=width // 2 - 90, y=1310, w=180, h=44, fill=(230, 230, 230), text_color=(20, 20, 20))
    img[1370:1390, :] = fx.SEPARATOR_COLOR

    # features風: アイコン+短文を横に3つ
    col_w2 = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (col_w2 + 40)
        fx.draw_icon_blob(img, cx, 1440, 56, color=(90, 90, 90))
        fx.draw_text_line(img, cx, 1520, width=col_w2 - 20, height=14, n_words=3)
        fx.draw_text_line(img, cx, 1550, width=col_w2 - 20, height=12, n_words=6)
    img[1770:1790, :] = fx.SEPARATOR_COLOR

    # footer (position=last): 3列のリンク一覧 + コピーライト
    fcol_w = (width - 160) // 3
    for i in range(3):
        cx = 80 + i * (fcol_w + 40)
        fx.draw_text_line(img, cx, 1830, width=fcol_w - 20, height=16, n_words=2)
        for j in range(3):
            fx.draw_text_line(img, cx, 1870 + j * 26, width=fcol_w - 40, height=12, n_words=2)
    fx.draw_text_line(img, x=width // 2 - 150, y=1945, width=300, height=12, n_words=4)

    return fx.encode_png(img)


def main():
    if len(sys.argv) != 2:
        print("usage: gen_fixtures_pr5.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "testimonials_page.png").write_bytes(testimonials_page_png())
    print(f"fixtures written to {out_dir}")


if __name__ == "__main__":
    main()

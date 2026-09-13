"""
Playwright(Node.js)側からアップロードに使う画像ファイルを、決定的な合成画像
ヘルパー(fixtures.py)を使ってディスクに書き出すCLI。

使い方:
    python3 gen_fixtures.py <出力ディレクトリ>

出力:
    <dir>/multi_band.png   - PR2/PR3手順1で使う「1枚のホームページ画像」
    <dir>/single_pair.png  - 結合・分割の最小ケース用（帯2つ）
    <dir>/mobile.png       - 縦長のモバイル幅デザイン
    <dir>/sidebar.png      - サイドバー型デザイン
    <dir>/design.gif       - 手順2「受け付けられない画像」用（GIF）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixtures as fx  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("usage: gen_fixtures.py <output_dir>", file=sys.stderr)
        sys.exit(1)
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "multi_band.png").write_bytes(fx.multi_band_design_png())
    (out_dir / "single_pair.png").write_bytes(fx.single_pair_design_png())
    (out_dir / "mobile.png").write_bytes(fx.mobile_design_png())
    (out_dir / "sidebar.png").write_bytes(fx.sidebar_design_png())
    (out_dir / "design.gif").write_bytes(fx.gif_bytes())

    print(f"fixtures written to {out_dir}")


if __name__ == "__main__":
    main()

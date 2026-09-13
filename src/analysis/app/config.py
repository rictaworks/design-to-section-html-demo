"""解析層の決定的しきい値・コード値を一元管理する（requirements.md 6章）。
数値・文字列リテラルは本ファイルに集約し、他モジュールはここから import して使うこと。
"""

# --- 6.2 受入検証（解析層の多層防御。主たる検証はアプリケーション層/Railsが行う） ---
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# --- 6.3 正規化 ---
WORK_WIDTH_MAX = 1200
MOBILE_ASPECT_RATIO_THRESHOLD = 0.7
DARK_LUMINANCE_THRESHOLD = 128

# --- 6.4 帯分割 ---
MIN_BAND_HEIGHT_PX = 48
MAX_BANDS = 40
HEADER_MAX_HEIGHT_RATIO = 0.08
HEADER_BOUNDARY_MIN_LIMIT_PX = 4
HEADER_BASELINE_TOLERANCE_RATIO = 0.6
HEADER_BOTTOM_PADDING_PX = 4
SIDEBAR_HEIGHT_RATIO = 0.8
SIDEBAR_WIDTH_RATIO = 0.3
BLANK_CONTENT_RATIO_THRESHOLD = 0.02
BLANK_MIN_RUN_PX = 8
COLOR_JUMP_THRESHOLD = 30.0
COLOR_JUMP_PERSIST_PX = 8
SMOOTHING_KERNEL_PX = 5

# --- 6.5 ブロブ分類 ---
FOREGROUND_COLOR_DIST_THRESHOLD = 24.0
MIN_BLOB_AREA_PX = 8

TEXT_MAX_HEIGHT_RATIO_OF_BAND = 0.15
TEXT_MAX_HEIGHT_PX = 40
TEXT_MIN_ASPECT = 1.5
TEXT_MAX_COLOR_STD = 30.0

IMAGE_MIN_AREA_RATIO_OF_BAND = 0.02
IMAGE_MIN_COLOR_STD = 20.0
CIRCLE_MIN_CIRCULARITY = 0.85

BUTTON_MIN_CONTRAST = 40.0
BUTTON_MAX_COLOR_STD = 20.0
BUTTON_MIN_WIDTH_PX = 40
BUTTON_MAX_WIDTH_PX = 320
BUTTON_MIN_HEIGHT_PX = 20
BUTTON_MAX_HEIGHT_PX = 80
# ボタン状は「内部に文字状ブロブを1つ含む」（6.5）。前景マスクの充填率が外接矩形の面積に
# ほぼ等しい（＝内部に穴＝ラベルが無い）場合は、単なる無地の矩形（見出し等）とみなし
# ボタンとしない。
BUTTON_MAX_FILL_RATIO = 0.95

ICON_MAX_SIZE_PX = 32
ICON_MIN_ASPECT = 0.7
ICON_MAX_ASPECT = 1.4
ICON_MAX_COLOR_STD = 15.0

# --- 6.5 帯特徴（列数・画像位置・整列） ---
COLUMN_GAP_MIN_PX = 40
COLUMN_GAP_RATIO_OF_WIDTH = 0.05
IMAGE_COVERAGE_RATIO = 0.8
IMAGE_POSITION_LEFT_MAX_RATIO = 0.35
IMAGE_POSITION_RIGHT_MIN_RATIO = 0.65
ALIGNMENT_CENTER_MIN_RATIO = 0.4
ALIGNMENT_CENTER_MAX_RATIO = 0.6

# --- 6.6 種別判定 ---
CONFIDENCE_ADOPT_THRESHOLD = 0.6
CONFIDENCE_LOW_THRESHOLD = 0.4
CONFIDENCE_CLOSE_DIFF = 0.05
HERO_MAX_BANDS_FROM_TOP = 2  # ヘッダーを除く先頭から2帯以内

# requirements.md 7章の12種別コード。アプリケーション層(Rails)のSectionKinds
# （src/backend/lib/section_kinds.rb）と文字列を完全に一致させること
# （解析層が返すdetected_kindをRailsのComponentCatalogが直接キーとして参照するため）。
SECTION_KINDS = [
    "header",
    "hero",
    "features",
    "image_with_text",
    "cta",
    "pricing",
    "testimonials",
    "faq",
    "gallery",
    "logos",
    "footer",
    "generic_text",
]

# --- 6.7 切り出し・埋め込み予算 ---
CROP_LONG_EDGE_PX = 800
CROP_LONG_EDGE_FALLBACK_PX = 400
EMBED_BUDGET_BYTES = 4 * 1024 * 1024
CROP_JPEG_QUALITY = 80

# --- notice_type コード（アプリケーション層と共有する） ---
NOTICE_MOBILE_DESIGN_DETECTED = "mobile_design_detected"
NOTICE_DARK_THEME_DETECTED = "dark_theme_detected"
NOTICE_NO_SEPARATOR_FOUND = "no_separator_found"
NOTICE_BAND_COUNT_EXCEEDED = "band_count_exceeded"
NOTICE_SIDEBAR_LAYOUT_DETECTED = "sidebar_layout_detected"
NOTICE_LOW_CONFIDENCE_KIND = "low_confidence_kind"
NOTICE_GENERIC_TEXT_FALLBACK = "generic_text_fallback"
NOTICE_CLOSE_CONFIDENCE_RUNNER_UP = "close_confidence_runner_up"
NOTICE_EMBEDDING_BUDGET_EXCEEDED = "embedding_budget_exceeded"
NOTICE_INCONSISTENT_VARIANT_FEATURES = "inconsistent_variant_features"

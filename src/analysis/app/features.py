"""6.5 帯特徴の集計（列数・反復項目数・画像位置・整列・見出し規模・背景色・アクセント色等）。"""
import statistics

from app import config
from app.blobs import extract_and_classify, band_background_color


def _to_hex(bgr: tuple) -> str:
    b, g, r = (int(round(c)) for c in bgr)
    return "#{:02x}{:02x}{:02x}".format(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _luminance(bgr: tuple) -> float:
    b, g, r = bgr
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def _cluster_columns(blobs: list, band_width: int) -> int:
    if not blobs:
        return 1
    gap_threshold = max(config.COLUMN_GAP_MIN_PX, band_width * config.COLUMN_GAP_RATIO_OF_WIDTH)
    spans = sorted((b.x, b.x + b.w) for b in blobs)
    clusters = 1
    current_max = spans[0][1]
    for start, end in spans[1:]:
        if start - current_max > gap_threshold:
            clusters += 1
            current_max = end
        else:
            current_max = max(current_max, end)
    return max(1, min(4, clusters))


def _image_position(image_blobs: list, band_width: int, band_height: int) -> str:
    if not image_blobs:
        return "none"
    left = min(b.x for b in image_blobs)
    right = max(b.x + b.w for b in image_blobs)
    top = min(b.y for b in image_blobs)
    bottom = max(b.y + b.h for b in image_blobs)
    union_w = right - left
    union_h = bottom - top
    center_x = (left + right) / 2

    covers_most = (
        union_w >= band_width * config.IMAGE_COVERAGE_RATIO
        and union_h >= band_height * config.IMAGE_COVERAGE_RATIO
    )
    if covers_most:
        return "full"
    if union_w >= band_width * config.IMAGE_COVERAGE_RATIO:
        return "top"
    if center_x < band_width * config.IMAGE_POSITION_LEFT_MAX_RATIO:
        return "left"
    if center_x > band_width * config.IMAGE_POSITION_RIGHT_MIN_RATIO:
        return "right"
    return "top"


def extract_band_features(
    band_image,
    position: str,
    work_width: int,
    work_height: int,
    band_top: int,
    band_bottom: int,
    accent_fallback: str = None,
) -> tuple:
    band_height, band_width = band_image.shape[:2]
    bg_color = band_background_color(band_image)
    blobs = extract_and_classify(band_image, bg_color)

    text_blobs = [b for b in blobs if b.kind == "text"]
    image_blobs = [b for b in blobs if b.kind == "image"]
    circle_blobs = [b for b in blobs if b.kind == "circle_image"]
    button_blobs = [b for b in blobs if b.kind == "button"]
    icon_blobs = [b for b in blobs if b.kind == "icon"]

    non_text_blobs = image_blobs + circle_blobs + button_blobs + icon_blobs
    column_count = _cluster_columns(non_text_blobs or text_blobs, band_width)

    repeat_candidates = [len(icon_blobs), len(circle_blobs), len(image_blobs), len(button_blobs)]
    repeat_count = max([column_count] + repeat_candidates)

    all_image_like = image_blobs + circle_blobs
    image_position = _image_position(all_image_like, band_width, band_height)

    if text_blobs:
        mean_x = sum(b.x + b.w / 2 for b in text_blobs) / len(text_blobs)
        alignment = (
            "center"
            if band_width * config.ALIGNMENT_CENTER_MIN_RATIO
            <= mean_x
            <= band_width * config.ALIGNMENT_CENTER_MAX_RATIO
            else "left"
        )
    else:
        alignment = "left"

    text_heights = [b.h for b in text_blobs]
    max_text_height = max(text_heights) if text_heights else 0
    median_text_height = int(statistics.median(text_heights)) if text_heights else 0
    heading_scale = (max_text_height / median_text_height) if median_text_height > 0 else 1.0

    accent_color_hex = None
    if button_blobs:
        accent_color_hex = _to_hex(button_blobs[0].mean_color)
    elif accent_fallback is not None:
        accent_color_hex = accent_fallback

    features = {
        "column_count": column_count,
        "repeat_count": repeat_count,
        "image_position": image_position,
        "alignment": alignment,
        "heading_scale": round(heading_scale, 3),
        "bg_color_hex": _to_hex(bg_color),
        "bg_luminance": round(_luminance(bg_color), 3),
        "accent_color_hex": accent_color_hex,
        "height_ratio": (band_bottom - band_top) / work_height if work_height else 0.0,
        "position": position,
        "text_blob_count": len(text_blobs),
        "max_text_blob_height": max_text_height,
        "median_text_blob_height": median_text_height,
        "button_blob_count": len(button_blobs),
        "icon_blob_count": len(icon_blobs),
        "image_blob_count": len(image_blobs),
        "circular_image_blob_count": len(circle_blobs),
    }
    return features, blobs

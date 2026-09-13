"""6.5 ブロブ抽出・分類。"""
import math
from dataclasses import dataclass

import cv2
import numpy as np

from app import config


@dataclass
class Blob:
    x: int
    y: int
    w: int
    h: int
    area: int
    mean_color: tuple
    color_std: float
    aspect: float
    circularity: float
    kind: str = None


def _background_color(band_image: np.ndarray) -> tuple:
    border = np.concatenate(
        [
            band_image[0, :, :],
            band_image[-1, :, :],
            band_image[:, 0, :],
            band_image[:, -1, :],
        ],
        axis=0,
    ).astype(np.int32)
    return tuple(int(c) for c in np.median(border, axis=0))


def extract_blobs(band_image: np.ndarray, bg_color: tuple = None) -> list:
    if bg_color is None:
        bg_color = _background_color(band_image)

    bg = np.array(bg_color, dtype=np.int32)
    diff = np.linalg.norm(band_image.astype(np.int32) - bg, axis=2)
    mask = (diff > config.FOREGROUND_COLOR_DIST_THRESHOLD).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)

    blobs = []
    for label_id in range(1, num_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])
        if area < config.MIN_BLOB_AREA_PX:
            continue
        x = int(stats[label_id, cv2.CC_STAT_LEFT])
        y = int(stats[label_id, cv2.CC_STAT_TOP])
        w = int(stats[label_id, cv2.CC_STAT_WIDTH])
        h = int(stats[label_id, cv2.CC_STAT_HEIGHT])

        component_mask = labels[y : y + h, x : x + w] == label_id
        region = band_image[y : y + h, x : x + w][component_mask]
        mean_color = tuple(float(c) for c in region.mean(axis=0))
        # チャンネル間の色差ではなく、画素間のばらつき（内部の色分散）のみを見る
        color_std = float(region.std(axis=0).mean())

        contour_mask = (component_mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(contour_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        circularity = 0.0
        if contours:
            largest = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest, True)
            c_area = cv2.contourArea(largest)
            if perimeter > 0:
                circularity = float(4 * math.pi * c_area / (perimeter * perimeter))

        blobs.append(
            Blob(
                x=x,
                y=y,
                w=w,
                h=h,
                area=area,
                mean_color=mean_color,
                color_std=color_std,
                aspect=w / h if h > 0 else 0.0,
                circularity=circularity,
            )
        )
    return blobs


def _contrast(mean_color: tuple, bg_color: tuple) -> float:
    return float(np.linalg.norm(np.array(mean_color) - np.array(bg_color)))


def classify_blob(blob: Blob, band_height: int, band_width: int, bg_color: tuple) -> str:
    band_area = max(1, band_height * band_width)

    is_image_sized = blob.area >= band_area * config.IMAGE_MIN_AREA_RATIO_OF_BAND
    if is_image_sized and blob.color_std >= config.IMAGE_MIN_COLOR_STD:
        if blob.circularity >= config.CIRCLE_MIN_CIRCULARITY:
            return "circle_image"
        return "image"

    if (
        blob.w <= config.ICON_MAX_SIZE_PX
        and blob.h <= config.ICON_MAX_SIZE_PX
        and config.ICON_MIN_ASPECT <= blob.aspect <= config.ICON_MAX_ASPECT
        and blob.color_std <= config.ICON_MAX_COLOR_STD
    ):
        return "icon"

    # ボタン状の条件（幅・高さ・彩度・コントラストすべてを要求）は文字状より狭く具体的なため、
    # 先に判定する。文字状を先に判定すると、帯が大きく text_max_height が40px近くまで
    # 緩む場合に、典型的なCTAボタン（高さ20〜40px程度）が文字状として誤判定され、
    # button_blob_count が過小評価されてしまう（CTA/pricing/hero判定の精度に直結する）。
    fill_ratio = blob.area / max(1, blob.w * blob.h)
    if (
        config.BUTTON_MIN_WIDTH_PX <= blob.w <= config.BUTTON_MAX_WIDTH_PX
        and config.BUTTON_MIN_HEIGHT_PX <= blob.h <= config.BUTTON_MAX_HEIGHT_PX
        and blob.color_std <= config.BUTTON_MAX_COLOR_STD
        and _contrast(blob.mean_color, bg_color) >= config.BUTTON_MIN_CONTRAST
        and fill_ratio <= config.BUTTON_MAX_FILL_RATIO
    ):
        return "button"

    text_max_height = min(config.TEXT_MAX_HEIGHT_PX, band_height * config.TEXT_MAX_HEIGHT_RATIO_OF_BAND)
    if (
        blob.h <= text_max_height
        and blob.aspect >= config.TEXT_MIN_ASPECT
        and blob.color_std <= config.TEXT_MAX_COLOR_STD
    ):
        return "text"

    return None


def band_background_color(band_image: np.ndarray) -> tuple:
    return _background_color(band_image)


def extract_and_classify(band_image: np.ndarray, bg_color: tuple = None) -> list:
    if bg_color is None:
        bg_color = _background_color(band_image)
    blobs = extract_blobs(band_image, bg_color)
    height, width = band_image.shape[:2]
    for blob in blobs:
        blob.kind = classify_blob(blob, height, width, bg_color)
    return blobs

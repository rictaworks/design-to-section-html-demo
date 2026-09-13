"""6.3 正規化：作業画像への縮小・テーマ判定・モバイル幅判定。"""
from dataclasses import dataclass, field

import cv2
import numpy as np

from app import config


@dataclass
class NormalizeResult:
    work_image: np.ndarray
    work_scale: float
    theme: str
    mobile_design: bool
    notices: list = field(default_factory=list)


def _composite_alpha_on_white(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 4:
        bgr = image[:, :, :3].astype(np.float32)
        alpha = (image[:, :, 3:4].astype(np.float32)) / 255.0
        white = np.full_like(bgr, 255.0)
        composited = bgr * alpha + white * (1.0 - alpha)
        return composited.astype(np.uint8)
    return image


def _border_pixels(image: np.ndarray) -> np.ndarray:
    top = image[0, :, :]
    bottom = image[-1, :, :]
    left = image[:, 0, :]
    right = image[:, -1, :]
    return np.concatenate([top, bottom, left, right], axis=0)


def _detect_theme(image: np.ndarray) -> str:
    border = _border_pixels(image)
    gray = cv2.cvtColor(border.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY).reshape(-1)
    counts = np.bincount(gray, minlength=256)
    mode_luminance = int(np.argmax(counts))
    return "dark" if mode_luminance < config.DARK_LUMINANCE_THRESHOLD else "light"


def normalize_image(image: np.ndarray) -> NormalizeResult:
    notices = []

    image = _composite_alpha_on_white(image)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    height, width = image.shape[:2]

    if width > config.WORK_WIDTH_MAX:
        work_scale = config.WORK_WIDTH_MAX / width
        work_width = config.WORK_WIDTH_MAX
        work_height = max(1, round(height * work_scale))
        work_image = cv2.resize(image, (work_width, work_height), interpolation=cv2.INTER_AREA)
    else:
        work_scale = 1.0
        work_image = image

    theme = _detect_theme(work_image)
    if theme == "dark":
        notices.append({"notice_type": config.NOTICE_DARK_THEME_DETECTED, "detail": {}})

    mobile_design = width < height * config.MOBILE_ASPECT_RATIO_THRESHOLD
    if mobile_design:
        notices.append({"notice_type": config.NOTICE_MOBILE_DESIGN_DETECTED, "detail": {}})

    return NormalizeResult(
        work_image=work_image,
        work_scale=work_scale,
        theme=theme,
        mobile_design=mobile_design,
        notices=notices,
    )

"""6.4 帯分割：行プロファイル・区切り候補・最小帯高/上限の適用・ヘッダー分離・サイドバー簡易対応。"""
from dataclasses import dataclass, field

import cv2
import numpy as np

from app import config
from app.blobs import extract_and_classify


@dataclass
class SegmentResult:
    band_ranges: list
    shell_layout: str
    sidebar_x: int
    notices: list = field(default_factory=list)


def _smooth(arr: np.ndarray, kernel: int) -> np.ndarray:
    if kernel <= 1:
        return arr
    kernel_vals = np.ones(kernel) / kernel
    return np.convolve(arr, kernel_vals, mode="same")


def compute_row_profile(image: np.ndarray, bg_color: tuple, x_start: int = 0, x_end: int = None) -> dict:
    if x_end is None:
        x_end = image.shape[1]
    region = image[:, x_start:x_end]
    bg = np.array(bg_color, dtype=np.int32)
    diff = np.linalg.norm(region.astype(np.int32) - bg, axis=2)
    content_ratio = (diff > config.FOREGROUND_COLOR_DIST_THRESHOLD).mean(axis=1)

    mean_color = region.reshape(region.shape[0], -1, 3).mean(axis=1)

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    sobel = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    edge_amount = np.abs(sobel).mean(axis=1)

    return {
        "content_ratio": _smooth(content_ratio, config.SMOOTHING_KERNEL_PX),
        "mean_color": mean_color,
        "edge_amount": _smooth(edge_amount, config.SMOOTHING_KERNEL_PX),
    }


def _blank_run_candidates(content_ratio: np.ndarray) -> list:
    candidates = []
    height = len(content_ratio)
    is_blank = content_ratio < config.BLANK_CONTENT_RATIO_THRESHOLD
    y = 0
    while y < height:
        if is_blank[y]:
            start = y
            while y < height and is_blank[y]:
                y += 1
            run_len = y - start
            spans_whole_image = start == 0 and y == height
            if run_len >= config.BLANK_MIN_RUN_PX and not spans_whole_image:
                candidates.append((start + y) // 2)
        else:
            y += 1
    return candidates


def _color_jump_candidates(mean_color: np.ndarray) -> list:
    candidates = []
    height = len(mean_color)
    for y in range(1, height):
        jump = float(np.linalg.norm(mean_color[y] - mean_color[y - 1]))
        if jump <= config.COLOR_JUMP_THRESHOLD:
            continue
        end = min(height, y + config.COLOR_JUMP_PERSIST_PX)
        if end - y < config.COLOR_JUMP_PERSIST_PX:
            continue
        persisted = np.linalg.norm(mean_color[y:end] - mean_color[y], axis=1)
        if np.all(persisted < config.COLOR_JUMP_THRESHOLD):
            candidates.append(y)
    return candidates


def _image_bottom_candidates(image: np.ndarray, bg_color: tuple, x_start: int, x_end: int) -> list:
    region = image[:, x_start:x_end]
    blobs = extract_and_classify(region, bg_color)
    candidates = []
    for b in blobs:
        if b.kind in ("image", "circle_image"):
            bottom = b.y + b.h
            if bottom < image.shape[0]:
                candidates.append(bottom)
    return candidates


def _merge_candidates(candidates: list, min_gap: int) -> list:
    if not candidates:
        return []
    ordered = sorted(set(candidates))
    merged = [ordered[0]]
    for c in ordered[1:]:
        if c - merged[-1] < min_gap:
            continue
        merged.append(c)
    return merged


def _ranges_from_boundaries(boundaries: list, height: int) -> list:
    points = [0] + boundaries + [height]
    return [(points[i], points[i + 1]) for i in range(len(points) - 1) if points[i + 1] > points[i]]


def _enforce_min_height(ranges: list) -> list:
    ranges = list(ranges)
    changed = True
    while changed:
        changed = False
        for i, (top, bottom) in enumerate(ranges):
            if bottom - top < config.MIN_BAND_HEIGHT_PX and len(ranges) > 1:
                if i == len(ranges) - 1:
                    prev_top, _ = ranges[i - 1]
                    ranges[i - 1] = (prev_top, bottom)
                    del ranges[i]
                else:
                    _, next_bottom = ranges[i + 1]
                    ranges[i] = (top, next_bottom)
                    del ranges[i + 1]
                changed = True
                break
    return ranges


def _enforce_max_bands(ranges: list) -> tuple:
    ranges = list(ranges)
    exceeded = len(ranges) > config.MAX_BANDS
    while len(ranges) > config.MAX_BANDS:
        heights = [b - t for t, b in ranges]
        i = int(np.argmin(heights))
        if i == len(ranges) - 1:
            prev_top, _ = ranges[i - 1]
            _, bottom = ranges[i]
            ranges[i - 1] = (prev_top, bottom)
            del ranges[i]
        else:
            top, _ = ranges[i]
            _, next_bottom = ranges[i + 1]
            ranges[i] = (top, next_bottom)
            del ranges[i + 1]
    return ranges, exceeded


def _detect_header_boundary(image: np.ndarray, bg_color: tuple) -> int:
    height, width = image.shape[:2]
    limit = int(height * config.HEADER_MAX_HEIGHT_RATIO)
    if limit < 4:
        return None
    top_region = image[0:limit, :]
    blobs = extract_and_classify(top_region, bg_color)
    text_blobs = [b for b in blobs if b.kind == "text"]
    if len(text_blobs) < 2:
        return None
    centers = [b.y + b.h / 2 for b in text_blobs]
    centers.sort()
    if centers[-1] - centers[0] > limit * 0.6:
        return None
    bottom = max(b.y + b.h for b in text_blobs) + 4
    return min(bottom, limit)


def _detect_sidebar(image: np.ndarray, bg_color: tuple) -> int:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobel_x = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    limit_x = max(1, int(width * config.SIDEBAR_WIDTH_RATIO))
    required_rows = int(height * config.SIDEBAR_HEIGHT_RATIO)

    edge_rows_per_col = (sobel_x > config.COLOR_JUMP_THRESHOLD).sum(axis=0)
    for x in range(1, limit_x):
        if edge_rows_per_col[x] >= required_rows:
            return x
    return None


def segment_bands(image: np.ndarray, bg_color: tuple) -> SegmentResult:
    notices = []
    height, width = image.shape[:2]

    sidebar_x = _detect_sidebar(image, bg_color)
    shell_layout = "single"
    x_start = 0
    if sidebar_x is not None:
        shell_layout = "sidebar"
        x_start = sidebar_x
        notices.append({"notice_type": config.NOTICE_SIDEBAR_LAYOUT_DETECTED, "detail": {"sidebar_width_px": sidebar_x}})

    profile = compute_row_profile(image, bg_color, x_start=x_start, x_end=width)

    candidates = []
    candidates += _blank_run_candidates(profile["content_ratio"])
    candidates += _color_jump_candidates(profile["mean_color"])
    candidates += _image_bottom_candidates(image, bg_color, x_start, width)

    header_boundary = _detect_header_boundary(image[:, x_start:width], bg_color)
    if header_boundary is not None:
        candidates.append(header_boundary)

    candidates = _merge_candidates(candidates, config.MIN_BAND_HEIGHT_PX)
    candidates = [c for c in candidates if 0 < c < height]

    if not candidates:
        notices.append({"notice_type": config.NOTICE_NO_SEPARATOR_FOUND, "detail": {}})
        ranges = [(0, height)]
    else:
        ranges = _ranges_from_boundaries(candidates, height)
        ranges = _enforce_min_height(ranges)

    ranges, exceeded = _enforce_max_bands(ranges)
    if exceeded:
        notices.append({"notice_type": config.NOTICE_BAND_COUNT_EXCEEDED, "detail": {}})

    return SegmentResult(band_ranges=ranges, shell_layout=shell_layout, sidebar_x=sidebar_x or 0, notices=notices)

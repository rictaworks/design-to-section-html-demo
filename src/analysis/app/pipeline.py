"""解析層のエンドツーエンド処理：/v1/analyze と /v1/refeature が呼び出す。"""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

from app import config
from app.normalize import normalize_image
from app.segment import segment_bands
from app.features import extract_band_features
from app.classify import classify_band
from app.crop import EmbedBudget, crop_blob
from app.blobs import band_background_color


class DecodeError(ValueError):
    pass


def decode_image_bytes(data: bytes) -> np.ndarray:
    try:
        pil_image = Image.open(io.BytesIO(data))
        pil_image.load()
        pil_image = ImageOps.exif_transpose(pil_image)
    except Exception as exc:  # noqa: BLE001 - 画像デコード失敗はすべて422にまとめる
        raise DecodeError("decode_failed") from exc

    if pil_image.mode == "RGBA":
        array = np.array(pil_image)
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGRA)

    pil_image = pil_image.convert("RGB")
    array = np.array(pil_image)
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)


def _allowed_kinds(position: str, index: int, header_offset: int) -> list:
    # 6.6「ヒーロー：ヘッダーを除く先頭から2帯以内」。ヘッダーが帯0として分離済みの場合は
    # header_offset=1となり、hero対象はindex 1,2。分離されていない場合はheader_offset=0で
    # index 0,1が対象になる（headerとheroは同じ帯を取り合う候補になりうるが、それは採点で決める）。
    allowed = list(config.SECTION_KINDS)
    if position != "first" and "header" in allowed:
        allowed.remove("header")
    if position != "last" and "footer" in allowed:
        allowed.remove("footer")
    if index >= header_offset + config.HERO_MAX_BANDS_FROM_TOP and "hero" in allowed:
        allowed.remove("hero")
    return allowed


def _classify_bands(work_image: np.ndarray, band_ranges: list, work_width: int, work_height: int) -> tuple:
    bands_out = []
    notices = []
    accent_fallback = None
    total = len(band_ranges)

    for index, (top, bottom) in enumerate(band_ranges):
        band_image = work_image[top:bottom, :]
        position = "first" if index == 0 else ("last" if index == total - 1 else "other")

        features, blobs = extract_band_features(
            band_image, position, work_width, work_height, top, bottom, accent_fallback
        )
        if accent_fallback is None and features["accent_color_hex"]:
            accent_fallback = features["accent_color_hex"]

        # bands_out[0]は既に分類済み（このループがindex 0から順に処理するため）なので、
        # ヘッダーが帯0として分離済みかどうかをここで安全に参照できる。
        header_offset = 1 if bands_out and bands_out[0]["detected_kind"] == "header" else 0
        allowed = _allowed_kinds(position, index, header_offset)
        kind, confidence, runner_up_kind, band_notices = classify_band(features, allowed)

        for notice in band_notices:
            notices.append({**notice, "band_position": index})

        bands_out.append(
            {
                "position": index,
                "top_y": top,
                "bottom_y": bottom,
                "features": features,
                "detected_kind": kind,
                "confidence": confidence,
                "runner_up_kind": runner_up_kind,
                "_blobs": blobs,
            }
        )

    return bands_out, notices


def _attach_crops(original_image: np.ndarray, work_scale: float, bands_out: list, notices: list) -> None:
    budget = EmbedBudget()
    for band in bands_out:
        image_blobs = [b for b in band["_blobs"] if b.kind in ("image", "circle_image")]
        crops = []
        flagged = False
        for blob in image_blobs:
            crop = crop_blob(original_image, work_scale, band["top_y"], blob, budget)
            crops.append(crop)
            if crop["placeholder"] and not flagged:
                notices.append(
                    {
                        "notice_type": config.NOTICE_EMBEDDING_BUDGET_EXCEEDED,
                        "detail": {},
                        "band_position": band["position"],
                    }
                )
                flagged = True
        band["crops"] = crops
        del band["_blobs"]


def analyze(image_bytes: bytes) -> dict:
    original_image = decode_image_bytes(image_bytes)
    # 透過は白へ合成する（6.2・6.3）。normalize_imageは作業画像(work_image)側では内部で合成
    # 済みだが、切り出し(_attach_crops)は original_image をそのまま参照するため、ここで一度だけ
    # 合成しておき、以降の処理全体（正規化・帯分割・特徴抽出・切り出し）で一貫させる。
    # refeature()も同じ理由で_composite_if_needed()を呼んでおり、両エンドポイントで対称にする。
    original_image = _composite_if_needed(original_image)
    norm = normalize_image(original_image)
    work_image = norm.work_image
    work_height, work_width = work_image.shape[:2]

    bg_color = band_background_color(work_image)
    seg = segment_bands(work_image, bg_color)

    notices = [dict(n, band_position=None) for n in norm.notices]
    notices += [dict(n, band_position=None) for n in seg.notices]

    bands_out, band_notices = _classify_bands(work_image, seg.band_ranges, work_width, work_height)
    notices += band_notices

    _attach_crops(original_image, norm.work_scale, bands_out, notices)

    return {
        "theme": norm.theme,
        "mobile_design": norm.mobile_design,
        "shell_layout": seg.shell_layout,
        "work_scale": norm.work_scale,
        "work_width": work_width,
        "work_height": work_height,
        "bands": bands_out,
        "notices": notices,
    }


def refeature(image_base64: str, work_scale: float, ranges: list) -> dict:
    import base64

    original_bytes = base64.b64decode(image_base64)
    original_image = decode_image_bytes(original_bytes)
    original_image = _composite_if_needed(original_image)

    oh, ow = original_image.shape[:2]
    work_width = max(1, round(ow * work_scale))
    work_height = max(1, round(oh * work_scale))
    work_image = cv2.resize(original_image[:, :, :3], (work_width, work_height), interpolation=cv2.INTER_AREA)

    band_ranges = [(int(r["top_y"]), int(r["bottom_y"])) for r in ranges]
    bands_out, notices = _classify_bands(work_image, band_ranges, work_width, work_height)
    _attach_crops(original_image[:, :, :3], work_scale, bands_out, notices)

    return {"bands": bands_out, "notices": notices}


def _composite_if_needed(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 4:
        bgr = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        white = np.full_like(bgr, 255.0)
        composited = (bgr * alpha + white * (1.0 - alpha)).astype(np.uint8)
        return composited
    return image

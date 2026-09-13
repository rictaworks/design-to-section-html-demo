"""6.7 切り出し・埋め込み予算制御：作業座標→元画像座標への復元、長辺縮小、4MB予算管理。"""
import base64

import cv2

from app import config


class EmbedBudget:
    def __init__(self, limit_bytes: int = config.EMBED_BUDGET_BYTES):
        self.limit_bytes = limit_bytes
        self.used_bytes = 0

    def try_consume(self, n: int) -> bool:
        if self.used_bytes + n <= self.limit_bytes:
            self.used_bytes += n
            return True
        return False


def _resize_long_edge(image, max_edge: int):
    h, w = image.shape[:2]
    long_edge = max(h, w)
    if long_edge <= max_edge:
        return image
    scale = max_edge / long_edge
    new_w, new_h = max(1, round(w * scale)), max(1, round(h * scale))
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _encode_jpeg_base64(image) -> tuple:
    # 予算(EmbedBudget)はHTMLへ実際に埋め込まれるサイズを管理するものなので、
    # base64エンコード前の生JPEGバイト数ではなく、エンコード後の文字列長で計測する
    # （base64はおよそ4/3倍に膨らむため、生バイト数で計測すると埋め込みサイズを過小評価する）。
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, config.CROP_JPEG_QUALITY])
    data = buf.tobytes()
    b64 = base64.b64encode(data).decode("ascii")
    return b64, len(b64)


def crop_blob(original_image, work_scale: float, band_top_work: int, blob, budget: EmbedBudget) -> dict:
    abs_top_work = band_top_work + blob.y
    abs_left_work = blob.x

    orig_left = int(round(abs_left_work / work_scale))
    orig_top = int(round(abs_top_work / work_scale))
    orig_w = max(1, int(round(blob.w / work_scale)))
    orig_h = max(1, int(round(blob.h / work_scale)))

    oh, ow = original_image.shape[:2]
    orig_left = max(0, min(orig_left, ow - 1))
    orig_top = max(0, min(orig_top, oh - 1))
    orig_w = min(orig_w, ow - orig_left)
    orig_h = min(orig_h, oh - orig_top)

    region = original_image[orig_top : orig_top + orig_h, orig_left : orig_left + orig_w]
    shape = "circle" if blob.kind == "circle_image" else "rect"

    for max_edge in (config.CROP_LONG_EDGE_PX, config.CROP_LONG_EDGE_FALLBACK_PX):
        resized = _resize_long_edge(region, max_edge)
        b64, size = _encode_jpeg_base64(resized)
        if budget.try_consume(size):
            return {
                "left_x": orig_left,
                "top_y": orig_top,
                "width": orig_w,
                "height": orig_h,
                "shape": shape,
                "image_base64": b64,
                "placeholder": False,
            }

    return {
        "left_x": orig_left,
        "top_y": orig_top,
        "width": orig_w,
        "height": orig_h,
        "shape": shape,
        "image_base64": "",
        "placeholder": True,
    }

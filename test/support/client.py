"""
アプリケーション層(Rails, :3001)へのHTTPクライアントヘルパー。

httpx.Client はインスタンスごとに Cookie jar を保持するため、同一インスタンス
を使い続ければ「同一セッション」を、複数インスタンスを作れば「別セッション
（別Cookie）」を素直に表現できる（requirements.md 11章のセッション分離確認に
そのまま使う）。

実行には httpx が必要（src/analysis/.venv に導入済み）。
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

BACKEND_URL = os.environ.get("D2H_BACKEND_URL", "http://localhost:3001")
ANALYSIS_URL = os.environ.get("D2H_ANALYSIS_URL", "http://localhost:8001")
FRONTEND_URL = os.environ.get("D2H_FRONTEND_URL", "http://localhost:3000")


def new_client(**kwargs) -> httpx.Client:
    return httpx.Client(base_url=BACKEND_URL, timeout=40.0, **kwargs)


@dataclass
class ApiResult:
    status_code: int
    json: Any
    response: httpx.Response


def create_conversion(
    client: httpx.Client, image_bytes: bytes, *, filename="design.png",
    content_type="image/png", honeypot: str | None = None,
) -> ApiResult:
    files = {"file": (filename, image_bytes, content_type)}
    data = {}
    if honeypot is not None:
        data["website"] = honeypot
    resp = client.post("/conversions", files=files, data=data)
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def list_conversions(client: httpx.Client) -> ApiResult:
    resp = client.get("/conversions")
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def get_conversion(client: httpx.Client, conversion_id: str) -> ApiResult:
    resp = client.get(f"/conversions/{conversion_id}")
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def delete_conversion(client: httpx.Client, conversion_id: str) -> ApiResult:
    resp = client.delete(f"/conversions/{conversion_id}")
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def source_image(client: httpx.Client, conversion_id: str) -> httpx.Response:
    return client.get(f"/conversions/{conversion_id}/source_image")


def update_band_kind(client: httpx.Client, conversion_id: str, band_id: str, kind: str) -> ApiResult:
    resp = client.patch(f"/conversions/{conversion_id}/bands/{band_id}", data={"kind": kind})
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def merge_band(client: httpx.Client, conversion_id: str, band_id: str, with_band_id: str) -> ApiResult:
    resp = client.post(f"/conversions/{conversion_id}/bands/{band_id}/merge", data={"with": with_band_id})
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def split_band(client: httpx.Client, conversion_id: str, band_id: str, y: int) -> ApiResult:
    resp = client.post(f"/conversions/{conversion_id}/bands/{band_id}/split", data={"y": y})
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def remove_band(client: httpx.Client, conversion_id: str, band_id: str) -> ApiResult:
    resp = client.post(f"/conversions/{conversion_id}/bands/{band_id}/remove")
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def restore_band(client: httpx.Client, conversion_id: str, band_id: str) -> ApiResult:
    resp = client.post(f"/conversions/{conversion_id}/bands/{band_id}/restore")
    return ApiResult(resp.status_code, _safe_json(resp), resp)


def wait_until_settled(client: httpx.Client, conversion_id: str, timeout: float = 30.0) -> ApiResult:
    """現行実装ではconversions#createもbands系アクションも同期処理で完了するため
    本来ポーリングは不要だが、フロントエンドと同じ「ACTIVE_STATESの間は待つ」
    考え方を安全側に倣うヘルパーとして用意する。"""
    deadline = time.monotonic() + timeout
    result = get_conversion(client, conversion_id)
    while result.json and result.json.get("state") in ("uploaded", "analyzing", "assembling", "reassembling"):
        if time.monotonic() > deadline:
            raise TimeoutError(f"conversion {conversion_id} did not settle in {timeout}s")
        time.sleep(0.5)
        result = get_conversion(client, conversion_id)
    return result


def _safe_json(resp: httpx.Response):
    if not resp.content:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def sorted_bands(conversion_json: dict) -> list[dict]:
    return sorted(conversion_json["bands"], key=lambda b: b["position"])


def listed_bands(conversion_json: dict) -> list[dict]:
    """ConversionPresenter#detail は Band.listed（削除済みは含むが置換済みのみ
    除く）を返す。削除済み帯は一覧に残ったまま state=="removed" になる
    （復元できるようにするため）。組み立て対象からの除外は Band.assemblable
    （state not in [removed, replaced]）で別途行われる。"""
    return sorted_bands(conversion_json)


def active_bands(conversion_json: dict) -> list[dict]:
    """組み立て対象（=画面上で「消えた」ように見える帯を除いたもの）に相当する
    削除済みを除いた一覧。"""
    return [b for b in sorted_bands(conversion_json) if b["state"] != "removed"]

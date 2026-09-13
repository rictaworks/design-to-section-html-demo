"""解析層（FastAPI）。画像と指示を受け取り結果を返すのみで、状態を持たない。"""
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app import config
from app.pipeline import analyze, refeature, DecodeError, InvalidRangeError

app = FastAPI(title="design-to-section-html-demo analysis service")


class RefeatureRange(BaseModel):
    top_y: int
    bottom_y: int


class RefeatureRequest(BaseModel):
    image_base64: str
    work_scale: float
    ranges: list[RefeatureRange]
    # 渡すrangesの先頭・末尾が、ページ全体の先頭・末尾の帯でもあるかどうか。
    # 帯編集（結合・分割）は一部の帯だけを解析層へ渡すため、ページ全体での位置関係は
    # アプリケーション層(Rails)側でしか分からず、明示的に伝える必要がある。
    is_first_band: bool = True
    is_last_band: bool = True


@app.post("/v1/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    # 解析層自体の多層防御（受入検証6.2の主たる実施はRails側）。上限+1byteだけ読み、
    # 超過していれば無制限に読み込む前に打ち切る。
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail={"error": "size_exceeded"})
    try:
        # analyze()はCPUバウンドな同期処理（OpenCV）のため、イベントループをブロックしない
        # よう別スレッドで実行する（同時リクエストが直列化されるのを防ぐ）。
        result = await run_in_threadpool(analyze, data)
    except DecodeError:
        raise HTTPException(status_code=422, detail={"error": "decode_failed"})
    return result


@app.post("/v1/refeature")
async def refeature_endpoint(payload: RefeatureRequest):
    try:
        result = await run_in_threadpool(
            refeature,
            payload.image_base64,
            payload.work_scale,
            [r.model_dump() for r in payload.ranges],
            is_first_band=payload.is_first_band,
            is_last_band=payload.is_last_band,
        )
    except DecodeError:
        raise HTTPException(status_code=422, detail={"error": "decode_failed"})
    except InvalidRangeError:
        raise HTTPException(status_code=422, detail={"error": "invalid_range"})
    return result

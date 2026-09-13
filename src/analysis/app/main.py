"""解析層（FastAPI）。画像と指示を受け取り結果を返すのみで、状態を持たない。"""
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import config
from app.pipeline import analyze, refeature, DecodeError

app = FastAPI(title="design-to-section-html-demo analysis service")


class RefeatureRange(BaseModel):
    top_y: int
    bottom_y: int


class RefeatureRequest(BaseModel):
    image_base64: str
    work_scale: float
    ranges: list[RefeatureRange]


@app.post("/v1/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    # 解析層自体の多層防御（受入検証6.2の主たる実施はRails側）。上限+1byteだけ読み、
    # 超過していれば無制限に読み込む前に打ち切る。
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=422, detail={"error": "size_exceeded"})
    try:
        result = analyze(data)
    except DecodeError:
        raise HTTPException(status_code=422, detail={"error": "decode_failed"})
    return result


@app.post("/v1/refeature")
async def refeature_endpoint(payload: RefeatureRequest):
    try:
        result = refeature(
            payload.image_base64,
            payload.work_scale,
            [r.model_dump() for r in payload.ranges],
        )
    except DecodeError:
        raise HTTPException(status_code=422, detail={"error": "decode_failed"})
    return result

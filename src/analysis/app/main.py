"""解析層（FastAPI）。画像と指示を受け取り結果を返すのみで、状態を持たない。"""
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

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
    data = await file.read()
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

import base64

from fastapi.testclient import TestClient

from app.main import app
from tests.fixtures.synth import blank_canvas, draw_text_line, encode_png

client = TestClient(app)


def _sample_png_bytes() -> bytes:
    img = blank_canvas(800, 1000, bg=(255, 255, 255))
    draw_text_line(img, x=20, y=400, width=400, n_words=5)
    return encode_png(img)


def test_analyze_endpoint_returns_200_with_expected_shape():
    files = {"file": ("design.png", _sample_png_bytes(), "image/png")}
    res = client.post("/v1/analyze", files=files)
    assert res.status_code == 200
    body = res.json()
    assert "bands" in body and "notices" in body


def test_analyze_endpoint_returns_422_for_invalid_image():
    files = {"file": ("bad.png", b"not-an-image", "image/png")}
    res = client.post("/v1/analyze", files=files)
    assert res.status_code == 422
    assert res.json()["detail"]["error"] == "decode_failed"


def test_refeature_endpoint_returns_200_with_bands():
    b64 = base64.b64encode(_sample_png_bytes()).decode("ascii")
    res = client.post(
        "/v1/refeature",
        json={"image_base64": b64, "work_scale": 1.0, "ranges": [{"top_y": 0, "bottom_y": 1000}]},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["bands"]) == 1

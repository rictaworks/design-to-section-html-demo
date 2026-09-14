# 解析層（FastAPI + OpenCV）。Railway では Dockerfile があればそれが使われる。
# Railpack（自動検出ビルド）が prepare 段階で失敗したため、backend と同じ Dockerfile ビルドに揃える。
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# opencv-python-headless の共有ライブラリ依存（slim イメージには入っていない）
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y libglib2.0-0 libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app

RUN groupadd --system --gid 1000 app && \
    useradd app --uid 1000 --gid 1000 --create-home --shell /bin/bash
USER 1000:1000

# Railway の私設ネットワークは IPv6 のみのため :: で待ち受ける。PORT はサービス変数で固定（8001）。
EXPOSE 8001
CMD ["sh", "-c", "uvicorn app.main:app --host :: --port ${PORT:-8001}"]

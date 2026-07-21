FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/backend ./src/backend
COPY data/stock ./data/stock

CMD ["/bin/sh", "-c", ".venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# syntax=docker/dockerfile:1
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ENV TTSPIPER_WEB_DIR=/app/web TTSPIPER_TOKENS_FILE=/data/tokens.json PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" HF_HOME=/models TTSPIPER_HOST=0.0.0.0 TTSPIPER_PORT=29320
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src ./src
COPY web ./web

EXPOSE 29320
CMD ["python", "src/app.py"]

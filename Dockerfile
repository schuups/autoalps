# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY src/ ./src/                          

RUN uv sync --frozen --no-dev             

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv 

COPY --chown=appuser:appgroup src/ ./src/

ENV PATH="/app/.venv/bin:/app/src:$PATH" \
    PYTHONPATH="/app" \             
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8888/sse').raise_for_status()"

CMD ["python", "-m", "src.server"]
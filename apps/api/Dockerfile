# Multi-stage build for the APAAR-SDMV API (prototype).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . /app
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=build /app/.venv /opt/venv
COPY --from=build /app /app

WORKDIR /app
RUN useradd --create-home api && mkdir -p /app/var/storage && chown -R api:api /app
USER api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# APAAR-SDMV developer entry points.

.PHONY: dev test seed build build-api build-web lint

# One-command local demo: Postgres + API + web console.
dev:
	cd apps/api && uv sync --quiet
	docker compose up --build

# API tests run on SQLite; no Postgres or network access is required.
test:
	cd apps/api && uv sync
	cd apps/api && uv run pytest

# Rebuild the deterministic synthetic dataset (implemented in a later phase).
seed:
	cd apps/api && uv sync
	cd apps/api && uv run python -m app.seed --reset

# Production web build.
build:
	cd apps/api && uv sync
	cd apps/api && uv run ruff check .
	cd apps/api && uv run pytest
	cd apps/web && npm ci
	cd apps/web && npm run build

build-api-image:
	docker compose build api

build-web-image:
	docker compose build web

# APAAR-SDMV developer entry points.
# All data is synthetic; all external integrations are mock/sandbox.

.PHONY: dev demo test test-api test-web e2e benchmark smoke seed reset build build-api build-web lint

# One-command local demo: Postgres + API (auto-seeded) + web console.
dev demo:
	docker compose up --build

# Full local test suite (API + web unit tests).
test: test-api test-web

# API tests run on SQLite; no Postgres or network access is required.
test-api:
	cd apps/api && uv sync
	cd apps/api && uv run ruff check .
	cd apps/api && uv run pytest

# Web unit tests, typecheck and lint.
test-web:
	cd apps/web && npm ci
	cd apps/web && npm run test -- --run
	cd apps/web && npm run typecheck
	cd apps/web && npm run lint

# Browser E2E; starts the API (fresh SQLite + seed) and Next dev server.
e2e:
	cd apps/web && npm run e2e

# 10,000-row synthetic validation benchmark (target < 300 seconds).
benchmark:
	cd apps/api && uv sync
	cd apps/api && uv run python ../../scripts/benchmark_validation.py

# Smoke-test an already running Docker/local stack.
smoke:
	./scripts/smoke.sh

# Rebuild the deterministic synthetic dataset (also runs on first compose boot).
seed reset:
	cd apps/api && uv sync
	cd apps/api && uv run python -m app.seed --reset

# Production web build plus all API checks.
build:
	cd apps/api && uv sync
	cd apps/api && uv run ruff check .
	cd apps/api && uv run pytest
	cd apps/web && npm ci
	cd apps/web && npm run test -- --run
	cd apps/web && npm run typecheck
	cd apps/web && npm run lint
	cd apps/web && npm run build

build-api:
	docker compose build api

build-web:
	docker compose build web

lint:
	cd apps/api && uv run ruff check .
	cd apps/web && npm run lint

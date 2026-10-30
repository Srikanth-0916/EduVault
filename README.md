# APAAR-SDMV (prototype)

**APAAR Student Data Management & Verification Platform — prototype.**

A working, demo-ready prototype of the regulatory data lifecycle described in
[`APAAR_Student_Data_Platform_PRD.md`](./APAAR_Student_Data_Platform_PRD.md):
institution onboarding → approved intake → enrolment submission → validation →
duplicate/capacity review → nodal attestation → AICTE review → reporting/audit →
consent-scoped external verification with expiring, revocable links.

> ⚠️ **All data is synthetic. All government integrations (APAAR/ABC/DigiLocker/
> NAD/AICTE) are mock/sandbox adapters.** This prototype is not certified for
> real student data and never presents a mock response as live verification.

## Quickstart

```bash
# API + Postgres + web console
docker compose up --build
# API health:        http://localhost:8000/api/v1/health
# Web console:       http://localhost:3000
# API docs (Swagger): http://localhost:8000/api/v1/docs
```

Local (no Docker):

```bash
make dev    # docker compose up (recommended path)
make test   # API tests on SQLite (no Postgres/network needed)
make seed   # build the deterministic synthetic dataset
make build  # production web build
```

## Repository layout

| Path | Purpose |
|---|---|
| `apps/api` | FastAPI service (Python 3.12, SQLAlchemy 2, Pydantic v2) |
| `apps/web` | Next.js 16 App Router console (React 19, Tailwind 4) |
| `docs/` | Design, plans, and this prototype's documentation |
| `data/` | Demo CSVs and fixtures (synthetic) |
| `.superpowers/` | Local delivery notes (not part of the product) |

## Conventions

- API base path `/api/v1`; responses are camelCase; errors use
  `{"error": {"code", "message", "details"}, "traceId"}`.
- APAAR identifiers are encrypted at rest (Fernet), keyed-HMAC searchable
  (HMAC-SHA256 lookup token), and only ever displayed as last-4. They never
  appear in logs, URLs, analytics, or exports, and are never used as auth.
- Every institution-owned query is scoped server-side; duplicate matches create
  review cases, never automatic cancellations or fraud labels.
- Verification links are opaque, hashed at rest, expiring, revocable, and every
  attempt is audited.

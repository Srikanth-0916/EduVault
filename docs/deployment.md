# Deployment and Operations Guide (Prototype)

> This is a prototype deployment guide. It does not satisfy AICTE production hosting, security, data-residency, or disaster-recovery requirements.

## Local quick start

### Docker Compose

```bash
cp .env.example .env        # optional; compose has development defaults
docker compose up --build
```

Services:

| Service | URL | Notes |
|---|---|---|
| Web | http://localhost:3000 | Next.js production build |
| API | http://localhost:8000 | FastAPI; Swagger at `/api/v1/docs` |
| PostgreSQL | localhost:5432 | user/password/db `apaar`/`apaar`/`apaar_sdmv` |

The API seeds the deterministic synthetic dataset automatically on first boot
when `ENV=development` and `AUTO_SEED=true` (the compose default). Seeding is
idempotent. To deliberately rebuild the dataset:

```bash
docker compose exec api python -m app.seed --reset
```

Run the end-to-end smoke test after the stack is healthy:

```bash
./scripts/smoke.sh
# or: make smoke
```

Stop:

```bash
docker compose down          # keep volumes
docker compose down -v       # delete database and storage volumes
```

### Local development (without Docker)

Backend:

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run python -m app.seed --reset
```

Use `DATABASE_URL=sqlite:///./var/local.db` for a quick no-Postgres run, or start Postgres first. Create `var/` if needed.

Frontend:

```bash
cd apps/web
npm ci
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run dev
```

Tests/build:

```bash
cd apps/api && uv run ruff check . && uv run pytest -v
cd apps/web && npm run test -- --run && npm run typecheck && npm run lint && npm run build
```

Browser and performance evidence:

```bash
cd apps/web && npx playwright install chromium   # first run only
cd apps/web && npm run e2e                        # API+web auto-start; saves screenshots
cd apps/api && uv run python ../../scripts/benchmark_validation.py
```

The Playwright suite uses a fresh SQLite database (`apps/api/var/e2e.db`) and the
synthetic seed. It writes screenshots to `docs/evidence/`. The benchmark uses a
throwaway SQLite database and does not touch a developer database.

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `ENV` | yes | `development`, `test`, `production`; production refuses dev defaults |
| `DATABASE_URL` | yes | `postgresql+psycopg://user:pass@host:5432/db` (SQLite allowed in dev/test only) |
| `JWT_SECRET` | yes | JWT signing secret |
| `APAAR_ENCRYPTION_KEY` | yes | Fernet key material for APAAR ciphertext |
| `APAAR_LOOKUP_KEY` | yes | HMAC key for exact-match lookup tokens |
| `RECEIPT_SIGNING_KEY` | yes | HMAC key for verification receipts |
| `CORS_ORIGINS` | yes | Comma-separated allowed browser origins |
| `WEB_BASE_URL` | yes | Public web origin used in student verification links |
| `AUTO_SEED` | no | Development-only synthetic seed at startup (default `true`) |
| `NEXT_PUBLIC_API_BASE_URL` | yes (web build) | Public API base URL |
| `WEB_PORT` | no | Published web port (default 3000) |

Production rules:

- Generate secrets with a CSPRNG and store them in a managed secret store, not `.env` in git or images.
- `APAAR_ENCRYPTION_KEY` must be a valid Fernet key; the prototype accepts a passphrase-derived default only in development. Use a documented KMS/HSM-backed key and rotation plan in production.
- Set `ENV=production`; startup fails if development defaults or a non-Postgres DB URL are used.
- Terminate TLS 1.2+ (prefer 1.3) at a reverse proxy/load balancer.
- Set strict CORS origins (no wildcard).

## Database

- Runtime: PostgreSQL 16.
- Prototype schema creation: SQLAlchemy `create_all`; no migrations. Do not use this for production.
- Production: add Alembic (or equivalent) migrations, review indexes, partitioning for large enrolment/audit tables, and backup/PITR.
- Suggested indexes already represented: institution+year, batch+row number, APAAR lookup token, programme+year, notification recipient+read state.
- Backups must be encrypted; restore tests are required before go-live.

## Storage

- Prototype: `var/storage` (private local volume `api_storage`).
- Production: S3-compatible private bucket with server-side encryption, object lock for evidence where appropriate, malware scanning, lifecycle/retention, and signed short-lived access.
- Never serve uploaded CSV or generated exports directly from a public path.

## Reverse proxy / web

- Route `/api/*` to FastAPI and everything else to Next.js, or expose them on separate subdomains with CORS.
- Next.js security headers are set in `next.config.ts`; add HSTS at the proxy.
- Do not cache authenticated API responses at the CDN.
- Public `/verify/<token>` responses must be `Cache-Control: no-store` and must not be indexed (`X-Robots-Tag: noindex`).

## Observability

Prototype:

- Structured logs with trace IDs.
- `GET /api/v1/health`.
- Audit table for material actions.

Production additions:

- OpenTelemetry traces/metrics, log aggregation, alerting on auth failures, cross-tenant attempts, bulk exports, public verification denials, queue backlog, provider failures.
- Dashboards for latency/error rate, validation throughput, review SLA, and data quality.
- Do not log request bodies for auth, upload, or verification routes; redact identifiers.
- The prototype installs a log filter that scrubs 12-digit APAAR-shaped
  sequences, bearer tokens and sensitive key/value pairs. Keep this as
  defence-in-depth, not as the only control.
- Security headers are attached to all API responses; the `Server` banner is
  removed. HSTS is added only when `ENV=production` and should also be set at
  the TLS proxy.

## Scaling

- API is stateless; scale horizontally behind a load balancer.
- Move validation/report/notification work to workers (Celery/RQ) with Redis and dead-letter queues.
- Use PostgreSQL read replicas for dashboards/reports if needed; pre-aggregate where scale demands.
- Rate limiting must move to Redis/WAF for multi-worker correctness.
- Prototype limits are login `10/min/IP` and public verification `30/min/IP`,
  returning `429 RATE_LIMITED` with `Retry-After`. The limiter is in-process and
  resets on restart.
- 10,000-row ingestion target: keep per-row work O(1) with prefetched maps;
  benchmark before go-live. The local synthetic benchmark completed upload +
  validation in ~12.3 seconds on SQLite (2026-10-31); this is prototype
  throughput, not a production SLA.

## Security operations

- MFA/OIDC for privileged users; short-lived tokens; refresh rotation.
- Key rotation and re-tokenization plan for APAAR lookup HMAC (rotation changes duplicate lookup tokens).
- Access recertification and break-glass procedure.
- Incident response, breach notification, and forensic preservation.
- Dependency/container scanning, SBOM, signed images.
- Independent penetration test and threat-model review before production.

## Disaster recovery

Prototype: no formal RPO/RTO. Production planning target from the PRD: RPO ≤ 15 minutes, RTO ≤ 4 hours, subject to AICTE agreement. Test restore, document runbooks, and define ownership.

## Demo reset

```bash
cd apps/api
uv run python -m app.seed --reset
```

This drops and recreates prototype tables in the configured database. Never point it at a database containing real data. The seed command prints only counts, never raw identifiers.

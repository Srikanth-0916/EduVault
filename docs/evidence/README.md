# Verification Evidence

> All data in these screenshots is synthetic. External integrations are mock/sandbox.

Generated on 2026-10-31 from the local prototype. The browser evidence is a
Chromium smoke run, not a cross-browser, load, penetration or accessibility
audit.

## Reproduce

```bash
make test       # API 119 tests + web 19 tests + typecheck + lint
make e2e        # 4 Playwright flows; regenerates the screenshots below
make benchmark  # 10,000-row upload + validation
make demo       # Docker stack, auto-seeded
make smoke      # full API lifecycle against the running stack
```

## Screenshots

| File | Flow | What it demonstrates |
|---|---|---|
| `login.png` | Public | Demo login with clearly labelled synthetic data and mock/sandbox claims |
| `institution-dashboard.png` | Institution operator | Approved intake separated into regular/supernumerary, reported vs approved, identity quality, mock labels |
| `aicte-dashboard.png` | AICTE reviewer | National aggregate dashboard with intake, review backlog and mock labels |
| `batch-results.png` | Institution operator | Upload/validation result with row findings and capacity evidence |
| `review-decision.png` | AICTE reviewer | Review decision recorded with reason after nodal submission |
| `student-share.png` | Student | Share authorized with claim scope, QR/link and signed receipt |
| `public-verification.png` | Public verifier | Only the granted claims, source/status and synthetic-demo notice |
| `denied-verification.png` | Public verifier | Generic denial after revocation, with no claim disclosure |

## Logs

| File | Contents |
|---|---|
| `smoke.txt` | Postgres-backed smoke transcript through upload, review, report export, verify and revoke |
| `benchmark-validation.txt` | Captured 10,000-row benchmark output |
| `demo-accounts.txt` | Login status for all 10 seeded demo accounts |

## Automated runs

| Run | Result |
|---|---|
| `uv run ruff check .` | clean |
| `uv run pytest` | 119 passed |
| `npm run test -- --run` | 19 passed in 6 files |
| `npm run typecheck` | clean |
| `npm run lint` | clean |
| `npm run build` | production build complete |
| `npx playwright test` | 4 passed in Chromium |
| `scripts/smoke.sh` (Docker/PostgreSQL) | `SMOKE PASS` through report export, verification and revocation |
| `scripts/benchmark_validation.py` | 10,000 rows, ~12.3 s, `READY_FOR_ATTESTATION` |

## Performance output

```
rows: 10,000
upload_seconds: 1.00
validation_seconds: 12.32
total_seconds: 13.31
status: READY_FOR_ATTESTATION
blocking_findings: 0
target_under_300_seconds: PASS
```

The run used a throwaway SQLite database seeded with the synthetic demo data.
It is not a PostgreSQL capacity test and does not establish a production SLA.

## Security smoke assertions

- Login is limited to 10 requests/min/IP and public verification to
  30 requests/min/IP; denials return `429` with `Retry-After`.
- API responses carry security headers and no `Server` banner.
- Uploads reject wrong extension/media type, >5 MB, >10,000 rows and invalid
  UTF-8 with clear errors; UTF-8 BOM is accepted.
- Log redaction removes APAAR-shaped digits, bearer tokens and sensitive
  key/value fields.
- Unknown, expired and revoked public verification tokens all return the same
  generic `410` payload and are audited.
- Public verification exposes no raw APAAR and includes a visible mock notice.

## Known gaps

See [`../limitations.md`](../limitations.md), [`../security.md`](../security.md)
and [`../accessibility.md`](../accessibility.md). The prototype has no
production KMS, MFA/OIDC, database encryption at rest, WAF, SIEM, malware
scanning, migration tooling or formal WCAG/penetration audit.

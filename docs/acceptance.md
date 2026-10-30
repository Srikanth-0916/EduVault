# MVP Acceptance Mapping

This maps PRD §22 acceptance criteria to evidence in the prototype. All data is
synthetic and every external integration is mock/sandbox.

## Final verification run (2026-10-31)

| Check | Result |
|---|---|
| API lint | `ruff check .` clean |
| API tests | 119 pytest tests passing on SQLite |
| Web unit tests | 19 Vitest tests in 6 files passing |
| Web type/lint/build | TypeScript, ESLint and Next production build clean |
| Browser E2E | 4 Playwright flows passing in Chromium |
| Performance | 10,000-row upload + validation in ~12.3 s (target < 300 s) |
| Smoke | `SMOKE PASS`: health, upload/validate, attest/submit, review, report export, share/verify/revoke against Docker + PostgreSQL |
| Demo accounts | All 10 seeded accounts return 200 on login (`docs/evidence/demo-accounts.txt`) |
| Evidence | Screenshots in `docs/evidence/` |

These are prototype results, not production certification or an SLA.

## Identity and access

| Criterion | Evidence |
|---|---|
| Institution and AICTE users sign in with separate role scopes | Auth API tests + seeded demo accounts + Playwright login |
| Institution users cannot access another institution's student records via UI/API | Tenant-isolation API tests; scoped queries |
| Privileged actions role-restricted and audited | Role guards + audit events on decisions/attestation/exports |

## Institution and intake master data

| Criterion | Evidence |
|---|---|
| AICTE can create institutions, campuses, programmes, intake snapshots | Master-data API tests + AICTE UI forms |
| Institution users can view but not edit approved intake | 403 test + read-only UI |
| Supernumerary capacity represented separately | Intake snapshot tests + programme table |

## Student records and ingestion

| Criterion | Evidence |
|---|---|
| Institution can create a student record manually | Student form + API test |
| Institution can upload CSV and inspect row-level results | Batch upload/validation tests + wizard + Playwright |
| Original file, uploader, checksum, time retained | Batch model fields + receipt |
| Invalid rows are not silently committed | Blocking-error submission test |
| Nodal attestation required before submission | 409 without attestation test + nodal-only guard + Playwright |
| CSV extension, media type, 5 MB and 10,000-row limits enforced | Upload-limit tests |
| UTF-8/BOM/header/encoding defects rejected clearly | Upload-limit tests |
| 10,000-row validation stays within target | `scripts/benchmark_validation.py` (~12.3 s synthetic) |

## APAAR validation and anomaly detection

| Criterion | Evidence |
|---|---|
| Basic 12-digit format validation, described as format only | `validate_apaar_format` tests + UI labels |
| Missing/malformed flagged | BR-001/BR-002 tests |
| Mock responses distinguishable from real verification | `mock:true`, `MOCK_APAAR`, banners |
| Intra-institution duplicates detected | BR-004 test + case |
| Cross-institution overlaps create cases, not fraud decisions | BR-005 test + resolution workflow |
| Intake excess calculated from correct snapshot | Capacity tests + evidence |
| NRI/OCI/FN distinct from seat classification | Attribute model + tests |

## Workflow and reporting

| Criterion | Evidence |
|---|---|
| AICTE can accept/return/reject with reason | Decision tests + review UI + Playwright |
| Institution can correct and resubmit returned batch | Return/resubmit test + editor |
| Dashboards show intake, enrolment, validation, cases | Dashboard endpoints + pages |
| Reports filter by year/institution/programme | Report API tests + UI filters |
| Analyst exports aggregate-only with suppression | Report tests + export audit test |
| CSV formula injection neutralized | `safe_csv_cell` tests |
| Exports audited | `REPORT_EXPORTED` audit test |

## Verification and security

| Criterion | Evidence |
|---|---|
| External verification shows only authorized claims | Public verify test + claim cards + Playwright |
| Expired/revoked references cannot disclose | 410 tests + denied state + Playwright revocation |
| Attempts/disclosures audited | Attempt/audit tests |
| APAAR masked in routine views, excluded from logs | Encryption/masking/log-redaction tests |
| Unknown, expired and revoked tokens are indistinguishable | Generic-410 tests |
| Login/public verification rate limits | Hardening tests + `Retry-After` |
| API security headers and no server banner | Hardening tests |
| Demo uses synthetic data only | Seed + banner + docs |

## Operations and delivery

| Criterion | Evidence |
|---|---|
| One-command local stack | `make demo` / `docker compose up --build` |
| Demo data available without manual DB edits | Development auto-seed; idempotent seed |
| End-to-end smoke can be repeated | `scripts/smoke.sh` |
| Browser flows reproducible | `apps/web/e2e/*.spec.ts` + `npm run e2e` |
| Accessibility intent and gaps documented | `docs/accessibility.md` |
| Production limitations are explicit | `docs/limitations.md`, `docs/security.md` |

## Manual demo acceptance

The automated browser run covers the main presentation path. A human-led
walkthrough is still recommended before a live demo.

- [ ] All key flows run without manual database edits.
- [ ] Mock integrations visibly labelled.
- [ ] One malformed APAAR, one duplicate, one intake exception, one verification request handled correctly.
- [ ] No institution sees another institution's private student data.
- [ ] Reviewer can explain every flag and next action.

# APAAR-SDMV Demo Script

> Synthetic data only. Every external check is a mock/sandbox adapter. The demo must never imply live APAAR/ABC/DigiLocker/NAD verification.

## Before the demo

1. `make demo` (or `docker compose up --build`). The API auto-seeds on first boot.
2. Confirm `http://localhost:8000/api/v1/health` returns `{"status":"ok"}`.
3. Confirm the web console at `http://localhost:3000` shows the “Synthetic demo data · Mock integrations” ribbon.
4. Optional reset: `docker compose exec api python -m app.seed --reset` (synthetic data only).
5. Optional automated rehearsal: `make smoke` and `make e2e` (screenshots in `docs/evidence/`).
6. Open two browsers or profiles: institution (AIT) and AICTE.

## Demo accounts

| Persona | Email | Password |
|---|---|---|
| Institution admin | `admin@demo-ait.edu` | `Demo@1234` |
| Institution operator | `operator@demo-ait.edu` | `Demo@1234` |
| Institution nodal officer | `nodal@demo-ait.edu` | `Demo@1234` |
| AICTE reviewer | `reviewer@aicte.demo` | `Demo@1234` |
| AICTE supervisor | `supervisor@aicte.demo` | `Demo@1234` |
| AICTE analyst | `analyst@aicte.demo` | `Demo@1234` |
| Auditor | `auditor@aicte.demo` | `Demo@1234` |
| Student | `student@demo-ait.edu` | `Demo@1234` |
| External verifier | `verifier@acme-demo.example` | `Demo@1234` |

## Story

Aarav Institute of Technology (Demo) submits its 2026-27 enrolment batch. The batch contains valid rows, a malformed APAAR value, a duplicate, and a possible cross-institution match. The operator corrects it, the nodal officer attests and submits, the AICTE reviewer returns one issue and accepts the rest, the duplicate case is resolved as a valid transfer, and the student shares a minimal enrolment claim with an employer.

## Sequence

### 1. Institution overview

Sign in as `operator@demo-ait.edu`. Point out:

- Approved regular and separately authorized supernumerary intake.
- Reported enrolment and capacity state.
- APAAR status breakdown with `Format valid` distinct from `Mock external check`.
- Pending batches and unresolved cases.

### 2. Upload a mixed batch

Go to **Batches → New batch**. Select 2026-27, main campus, upload `data/demo/batch_mixed.csv` (or use “Use bundled sample”). Show:

- SHA-256 checksum, uploader, timestamp, row count.
- Staging result and validation run.
- Row-level findings: malformed APAAR (`BR-002`), duplicate in batch (`BR-003`), same-institution duplicate (`BR-004`), cross-institution overlap (`BR-005`), possible excess (`BR-008`).
- Every finding has a rule ID, plain-language message, and next action.

### 3. Correct and resubmit

Edit the malformed row inline, replace the APAAR with a valid 12-digit test value, and revalidate. Explain that blocking errors prevent submission and warnings remain visible. If the batch is returned, show that editing creates a new revision and preserves the timeline.

### 4. Capacity and supernumerary

Open **Programmes & Intake** and a programme with a possible excess. Show:

- Approved regular seats.
- Authorized supernumerary seats as a separate line with approval reference.
- Reported count, exclusions, and `POSSIBLE_EXCESS` evidence.
- NRI/OCI/FN attributes are not seat classifications.

### 5. Attest and submit

Sign in as `nodal@demo-ait.edu`. Open the batch, show the attestation dialog (name + declaration), attest, then submit. Show the submission receipt (HMAC signature, checksum, counts) and status `UNDER_AICTE_REVIEW`.

### 6. AICTE review

Sign in as `reviewer@aicte.demo`. Open **Review Queue**, filter by institution/severity. Open the batch:

- Summary and row-level masked evidence.
- Capacity evidence and duplicate case links.
- Decision panel: accept / return for correction / reject, with reason code and free text.
- Return one issue and accept the remainder only if workflow policy permits; otherwise demonstrate return → correction → accept.

### 7. Cross-institution duplicate / transfer

Open **Cases**. Show the case with masked APAAR, two institutions, admission/exit dates, overlap days, and status. Resolve the non-overlapping case as `VALID_TRANSFER`. Emphasize: no automatic fraud label, no automatic cancellation, full history retained.

### 8. National dashboard and reports

Sign in as `supervisor@aicte.demo` or `analyst@aicte.demo`:

- National KPIs: reporting institutions, enrolment, possible excess, missing APAAR, open cases, review backlog.
- Intake vs reported chart, quality trend, institution drill-down.
- Reports: filter by year/programme, generated-at/freshness note, suppression note.
- Analyst CSV export is aggregate-only and audited; institution export is scoped and masked.

### 9. Student-controlled verification

Sign in as `student@demo-ait.edu`:

- View masked identity, enrolment, and distinct status chips.
- Create a share for “Acme Demo Pvt Ltd”, purpose “Employment screening”, claims Institution + Programme + Enrolment status, 24 hours.
- Review the disclosure summary and authorize.
- Show QR + copy link + expiry countdown + signed receipt download.

Open the link in a private window. The share card shows a QR code and a link to the public `/verify/<opaque-token>` page (never the raw API URL or APAAR). Show only the granted claims, each with source/status, the demo/mock banner, and receipt download. Point out no name, local ID, DOB, or full APAAR.

### 10. Revocation / expiry

Revoke the share from the student portal. Reload the public link: generic denial, no claim leakage. Show the verification attempt in the audit trail. The same generic denial applies to unknown and expired tokens; use `/verify/not-a-real-token` to demonstrate without waiting for expiry.

### 11. Audit trail

Sign in as `auditor@aicte.demo`. Filter audit events by batch/case/verification. Show actor, role, action, timestamp, reason, and masked metadata. No edit/delete controls exist.

## Fallbacks

- If Docker is unavailable, run API + web locally per README and use seeded SQLite.
- If the CSV upload is unavailable, create the mixed scenarios through the single-student form / seeded data.
- If external email is unavailable, in-app notifications are the source of truth; email delivery is mock-labelled.
- If the QR scanner is unavailable, copy the verification URL.

## Success criteria

- No manual database edits needed.
- Mock integrations visibly labelled.
- Malformed APAAR, duplicate, cross-institution overlap, intake exception, and verification lifecycle handled correctly.
- No cross-institution student data visible.
- Every flagged case has an explainable rule/evidence and a review path.

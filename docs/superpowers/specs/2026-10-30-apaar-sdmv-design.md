# APAAR-SDMV Prototype — Design

**Date:** 2026-10-30  
**Status:** Approved for implementation by the delivery request (build the PRD, phased, subagent-driven)  
**Source specification:** [`APAAR_Student_Data_Platform_PRD.md`](../../../APAAR_Student_Data_Platform_PRD.md)  
**Plan:** [`docs/superpowers/plans/2026-10-30-apaar-sdmv.md`](../plans/2026-10-30-apaar-sdmv.md)

## 1. Intent

Build a working, demo-ready prototype of the APAAR Student Data Management & Verification Platform described in the PRD. The prototype must demonstrate the *regulatory data lifecycle*, not just CRUD:

institution onboarding → approved intake → student/CSV submission → staging and validation → APAAR format/mock external checks → duplicate and capacity review → nodal attestation → AICTE review and decision → correction/resubmission → dashboards/reports/audit → consent-scoped external verification with expiring/revocable links.

All data is synthetic. All external government integrations are clearly labelled mock/sandbox adapters. The prototype must never claim that a mock response is a real APAAR/ABC/DigiLocker/NAD verification.

## 2. Goals, non-goals, anti-goals

### Goals

- Cover every P0 item in PRD §7 and the MVP acceptance criteria in §22.
- Demonstrate institution tenant isolation and server-side authorization on every route.
- Keep APAAR identifiers encrypted at rest, keyed-HMAC searchable, masked in UI/exports/logs, and never used as authentication.
- Make every consequential action explainable and auditable: rule ID, severity, evidence, actor, reason, timestamp.
- Provide a polished, responsive, accessible administrative UI with role-specific portals.
- Run locally with one command (`docker compose up`) and in tests without external services.

### Non-goals

- Live APAAR/ABC/DigiLocker/NAD/Aadhaar/AICTE integrations.
- Real identity proofing, real MFA enrolment, real email delivery, production key management.
- Degree, marksheet, transcript, or certificate issuance.
- Automated fraud findings or automatic cancellation of student records.
- National-scale HA deployment; production hardening is documented as a follow-on.

### Anti-goals

- A single green “Verified” badge that conflates format validity, external verification, institution record acceptance, and credential verification.
- Institution A reading Institution B's student rows.
- Silently accepting rows with blocking validation errors.
- Treating a mock response as `EXTERNALLY_CONFIRMED` without a visible `MOCK/SANDBOX` label.
- Storing raw APAAR numbers in logs, analytics payloads, URLs, or report exports.

## 3. Decisions taken

These are the calls made for the prototype. They are implementation decisions, not claims about AICTE policy.

| Area | Decision | Rationale |
|---|---|---|
| Repository shape | Monorepo: `apps/api` + `apps/web` + `docs` + `data` | Clear boundary, independent test/build, one compose file |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, PyJWT, Argon2, Fernet + HMAC | PRD recommendation; strong validation and testability |
| Database | PostgreSQL 16 in compose; SQLite for unit tests | Relational integrity in runtime; fast hermetic tests |
| Frontend | Next.js 16 App Router, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Recharts, Radix primitives | PRD recommendation; reusable role portals |
| Auth | Email/password + short-lived JWT; role memberships; MFA-ready fields. Demo passwords only, clearly labelled | Prototype without an external IdP; production IdP documented |
| Sessions | JWT held in browser storage for the prototype; all API calls use Bearer tokens | Avoids a fake OIDC dependency. Production note: move to httpOnly cookies/OIDC |
| Jobs | Synchronous validation and report generation; notification fan-out inline | 10k rows must stay under the NFR; avoids Redis/Celery operational burden in prototype |
| Files | Private local object-store abstraction under `var/storage`; SHA-256 checksum; no public serving | Mirrors S3/MinIO boundary without extra container |
| Duplicate lookup | `HMAC-SHA256(APAAR, APAAR_LOOKUP_KEY)`; raw value Fernet-encrypted; UI shows last 4 only | Low-entropy identifier cannot use an unkeyed hash |
| Mock APAAR | `MockApaarProvider`, deterministic outcomes, visible `mock: true` + adapter version | Demonstrates adapter contract without fabricating live verification |
| Consent/tokens | Opaque 32-byte URL-safe token; store SHA-256 hash + JWT jti; expiry and revocation server-side; single-use optional | Unguessable, revocable, auditable |
| Signed receipt | HMAC-SHA256 canonical JSON with `RECEIPT_SIGNING_KEY`, key id, issued/expiry timestamps | Demonstrates signed receipt without a PKI claim |
| Reporting | Aggregate-by-default; analyst never receives direct identifiers; institution-scoped student export for authorized institution roles; CSV only | Field-level and small-group controls fit MVP |
| Audit | Append-only application table; no update/delete routes; masked metadata; request IP/user-agent/trace ID | Traceability without overclaiming tamper-proof storage |
| Deployment | Docker Compose (Postgres, API, web); CI runs API tests + web build | Repeatable demo and review |
| Locale | English only; copy uses Indian academic conventions (academic year `2026-27`, INR not relevant) | MVP scope |

## 4. Roles and demo accounts

The role names are canonical API values.

| Role | Scope | Demo account |
|---|---|---|
| `INSTITUTION_ADMIN` | Own institution | `admin@demo-ait.edu` / `Demo@1234` |
| `INSTITUTION_OPERATOR` | Own institution | `operator@demo-ait.edu` / `Demo@1234` |
| `INSTITUTION_NODAL_OFFICER` | Own institution | `nodal@demo-ait.edu` / `Demo@1234` |
| `AICTE_REVIEWER` | Assigned institutions / national review | `reviewer@aicte.demo` / `Demo@1234` |
| `AICTE_SUPERVISOR` | National review + master data | `supervisor@aicte.demo` / `Demo@1234` |
| `AICTE_ANALYST` | Aggregated analytics | `analyst@aicte.demo` / `Demo@1234` |
| `SYSTEM_ADMIN` | Technical configuration | `sysadmin@aicte.demo` / `Demo@1234` |
| `AUDITOR` | Read-only audit | `auditor@aicte.demo` / `Demo@1234` |
| `STUDENT` | Own linked record and sharing | `student@demo-ait.edu` / `Demo@1234` |
| `EXTERNAL_VERIFIER` | Consented verification transaction only | `verifier@acme-demo.example` / `Demo@1234` |

Seed data uses three clearly synthetic institutions: **Aarav Institute of Technology (Demo)**, **Bharat Institute of Engineering (Demo)**, and **Chitra Institute of Management (Demo)**. The UI must display a persistent demo/mock banner.

## 5. Architecture

```text
Browser (Next.js 16)
  ├── /login, institution portal, AICTE portal, student portal, verifier
  ├── TanStack Query + typed API client (Bearer JWT)
  └── /verify/[token] public minimal result page
        │ HTTPS/JSON, CORS in dev
        ▼
FastAPI (/api/v1)
  ├── auth + RBAC + tenant scope dependencies
  ├── institutions / campuses / programmes / intake snapshots
  ├── enrollments + version history
  ├── submission batches (CSV staging, validation runs/findings)
  ├── duplicate cases + review decisions
  ├── dashboards / reports / exports
  ├── verification requests, consent grants, public token resolution
  ├── notifications / audit
  └── adapters: ApaarVerificationProvider (MockApaarProvider), NotificationProvider
        │
        ├── PostgreSQL 16 (transactional data)
        └── private local storage (source CSV + generated receipts)
```

### 5.1 Backend modules

- `app/main.py` — app factory, CORS, security headers, error handlers, health, router registration.
- `app/config.py` — pydantic-settings; secrets from env with safe dev defaults; fail closed in production.
- `app/db.py` — engine/session; `create_all` for prototype; SQLite test support.
- `app/models/` — SQLAlchemy models grouped by domain: master data, identity, enrollment, batch, review, verification, ops.
- `app/schemas/` — Pydantic request/response models with camelCase aliases.
- `app/deps.py` — current user, role guard, institution scope, pagination.
- `app/security.py` — Argon2 hashing, JWT encode/decode, APAAR encryption/HMAC, opaque tokens, receipt signing.
- `app/audit.py` — `record_audit(...)` helper; no raw sensitive values.
- `app/services/` — `validation`, `duplicates`, `capacity`, `reports`, `verification`, `notifications`, `csv_import`, `storage`.
- `app/adapters/` — provider protocols + mock implementations. Adapter results never mutate identity status to a live-verified state.
- `app/seed.py` — deterministic synthetic dataset and demo scenarios.

### 5.2 Data model (physical prototype)

Core tables mirror PRD §10 with these concrete choices:

- UUID string primary keys (`uuid4`), UTC timestamps, `created_at`/`updated_at`.
- String enum columns (no native DB enums) for portability.
- `Institution`, `Campus`, `Programme`, `ApprovalSnapshot`, `IntakeAllocation`.
- `User`, `OrganizationMembership`, `StudentIdentity`, `StudentEnrollment`, `EnrollmentVersion`.
- `SubmissionBatch`, `SubmissionRow`, `ValidationRun`, `ValidationFinding`.
- `DuplicateCase`, `IdentityVerification`.
- `ConsentGrant`, `VerificationRequest`, `VerificationReceipt`, `VerificationAttempt`.
- `AuditEvent`, `Notification`, `ReportExport`, `IntegrationClient` (seeded/read-only for MVP).

Key invariants:

- Every institution-owned row is reached through the authenticated membership's institution unless the actor is an authorized AICTE role.
- `StudentIdentity.apaar_lookup_token` is unique; cross-institution duplicates therefore share an identity row.
- `StudentEnrollment` has `version`, `is_current`, `supersedes_id`; every accepted change writes an `EnrollmentVersion` snapshot.
- Batch statuses: `DRAFT`, `VALIDATING`, `VALIDATION_FAILED`, `READY_FOR_ATTESTATION`, `SUBMITTED`, `UNDER_AICTE_REVIEW`, `RETURNED_FOR_CORRECTION`, `ACCEPTED`, `REJECTED`.
- Batch rows are never committed as accepted enrollments until attestation + submission; AICTE acceptance is separate.
- Row status: `PENDING`, `VALID`, `WARNING`, `ERROR`.
- Identity status: `MISSING`, `MALFORMED`, `FORMAT_VALID`, `PENDING_EXTERNAL_CHECK`, `EXTERNALLY_CONFIRMED`, `EXTERNAL_MISMATCH`, `EXTERNAL_UNAVAILABLE`, `MANUAL_REVIEW`, `CORRECTED`.
- Capacity states: `WITHIN_APPROVED_INTAKE`, `WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY`, `POSSIBLE_EXCESS`, `MISSING_APPROVAL_DATA`, `PENDING_RULE_REVIEW`.

### 5.3 API surface

Base path `/api/v1`. JSON unless noted. Errors: `{ "error": { "code", "message", "details" }, "traceId" }`.

- Auth: `POST /auth/login`, `GET /auth/me`.
- Master data: `GET /institutions/me`, `GET /institutions/me/campuses`, `GET /institutions/me/programmes`, `GET /institutions/me/intake`, `GET /institutions/me/users`, `POST /institutions/me/users/invitations`; AICTE: `GET/POST /institutions`, `GET /institutions/{id}`, `POST /institutions/{id}/campuses`, `POST /campuses/{id}/programmes`, `GET /programmes`, `POST /programmes/{id}/intake-snapshots`, `GET /intake`, `PATCH /intake-allocations/{id}`.
- Enrolments: `GET/POST /enrollments`, `GET/PATCH /enrollments/{id}`, `POST /enrollments/{id}/verify-identity`, `GET /students/me`.
- Batches: `GET/POST /submission-batches`, `POST /submission-batches/{id}/file` (multipart CSV), `POST /submission-batches/{id}/validate`, `GET /submission-batches/{id}`, `GET /submission-batches/{id}/results`, `PATCH /submission-batches/{id}/rows/{rowId}`, `POST /submission-batches/{id}/attest`, `POST /submission-batches/{id}/submit`, `POST /submission-batches/{id}/decision`, `GET /submission-batches/template.csv`, `GET /submission-batches/{id}/receipt`.
- Cases: `GET /duplicate-cases`, `GET /duplicate-cases/{id}`, `POST /duplicate-cases/{id}/resolve`, `POST /duplicate-cases/{id}/request-information`.
- Dashboards: `GET /dashboard/institution`, `GET /dashboard/national`.
- Reports: `GET /reports/enrolment`, `GET /reports/intake-reconciliation`, `GET /reports/data-quality`, `GET /reports/{type}/export.csv`.
- Verification: `POST /verification-requests`, `GET /verification-requests`, `GET /verification-requests/{id}`, `POST /verification-requests/{id}/authorize`, `POST /verification-requests/{id}/revoke`, `GET /public/verify/{token}`.
- Ops: `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `GET /audit-events`, `GET /health`.

### 5.4 Validation rules (rule set `2026.1`)

| Rule | Behaviour |
|---|---|
| `BR-001` | Missing APAAR → warning + `MISSING`; allowed only as pending-identifier row |
| `BR-002` | Not exactly 12 ASCII digits → blocking error + `MALFORMED` |
| `BR-003` | Same APAAR repeated in batch → blocking duplicate rows, no double count |
| `BR-004` | Same APAAR in same institution with overlapping period → high-severity case |
| `BR-005` | Same APAAR at another institution → case (high if active dates overlap, low if non-overlapping transfer context) |
| `BR-006` | Admission date after exit date → blocking error |
| `BR-007` | Programme/campus not mapped to institution or year → blocking error |
| `BR-008` | Programme/year count would exceed approved + authorized supernumerary → high-severity finding |
| `BR-009` | Supernumerary without approval reference → blocking error |
| `BR-010` | NRI/OCI/FN combination outside configured policy flags → review warning; attributes remain distinct |
| `BR-011` | Mock adapter unavailable → `EXTERNAL_UNAVAILABLE`, never confirmed |
| `BR-012` | Mock mismatch → `EXTERNAL_MISMATCH` + manual review |
| `BR-013` | Correction of accepted record → new version + revalidation + audit |
| `BR-014` | Cross-tenant access attempt → 403 + security audit event |
| `BR-015` | Expired/revoked/consumed token → 410 denial + audit attempt |

Capacity calculation granularity is `institution + campus + programme + academic year + approval snapshot + seat classification`. Regular and supernumerary allocations are separate. NRI/OCI/FN are attributes, never aliases for a seat classification.

### 5.5 Verification claims

Allowed claims: `INSTITUTION`, `PROGRAMME`, `ACADEMIC_YEAR`, `ENROLMENT_STATUS`, `RECORD_ACCEPTANCE`, `APAAR_FORMAT_STATUS`, `APAAR_EXTERNAL_STATUS` (only when the stored status exists; mock is labelled). Each returned claim carries `value`, `source`, `status`, `asOf`. The verifier view includes only the granted claims, a mock/demo banner, expiry, and a downloadable signed JSON receipt. Denials are generic and do not reveal whether a token once existed.

## 6. UX direction

- Administrative, trustworthy, data-dense but calm. Deep navy/ink sidebar, warm off-white canvas, teal primary, amber/red reserved for review states.
- Type: `Sora` for display headings, `Public Sans` for body/table numerics (Next/font).
- Persistent “Synthetic demo data · Mock integrations” ribbon.
- Separate visual identity for the public verification result: minimal, print-friendly, explicit claim-by-claim source labels.
- Status is never a single badge: distinct chips for APAAR format, external check (mock), record acceptance, credential verification.
- WCAG 2.1 AA intent: semantic landmarks, visible focus, labelled forms, contrast ≥ 4.5:1, keyboard-operable dialogs, no color-only status.
- Responsive: sidebar collapses under 1024 px; tables scroll or become cards; all primary flows usable at 390 px.

## 7. Security and privacy posture

- Secrets via env, never in source. Dev defaults are clearly non-production. `config.py` refuses default secrets when `ENV=production`.
- Argon2 password hashes, 30-minute JWT, role checks server-side, institution scoping on every object lookup.
- APAAR: Fernet ciphertext, keyed HMAC lookup token, last-4 masking only; no raw identifier in audit metadata, logs, URLs, or exports.
- Uploads: extension/content-type/size checks, 10,000-row limit, checksum, private storage, CSV formula injection neutralized on export.
- Verification tokens: 32 random bytes, hashed at rest, server-side expiry/revocation, every attempt logged. Rate limits on login and public verify.
- Audit table append-only via API; no mutation/deletion endpoints. Sensitive metadata excluded.
- The prototype is not certified for real student data. Documentation states this repeatedly.

## 8. Testing and acceptance

- Backend: pytest with SQLite; factory fixtures for roles/institutions; tests for auth, tenant isolation, validation rules, duplicate cases, capacity, batch workflow, verification expiry/revoke, audit, reports, upload limits, idempotency.
- Frontend: TypeScript strict, ESLint, production build; component/unit tests where valuable; Playwright smoke for login → upload → submit → review → verify when browsers are available.
- Manual evidence: seed script, demo CSV, curl smoke, browser screenshots of key screens.
- Definition of done follows PRD §23: server-side authorization, validations, audit events, sensitive-data protection, tests for success/failure/unauthorized paths, docs, accessibility/responsive check, synthetic data only.

## 9. Delivery phases

1. **Foundation & access** — monorepo, database, auth/RBAC, seed core, app shell, login.
2. **Master data & ingestion** — master data, enrolments, APAAR crypto/mock adapter, CSV staging, validation, duplicates, capacity, institution portal.
3. **AICTE workflow & analytics** — review decisions, case management, dashboards, reports, notifications, audit, AICTE portal.
4. **Controlled verification** — consent, opaque links/QR, signed receipts, verifier view, student portal.
5. **Hardening & demo** — security/perf/accessibility, e2e, docs, Docker smoke, final review.

Each phase ends with tests, a commit, and a push to `origin/main`.

## 10. Risks and mitigations in this prototype

| Risk | Mitigation |
|---|---|
| Mock results mistaken for live verification | `mock: true` everywhere, adapter labels, demo banner, docs |
| CSV validation performance | Prefetch maps, bulk inserts, 10k benchmark |
| Cross-tenant leaks | Central `assert_institution_access` + tests for every resource family |
| Token leakage | Hash at rest, no raw token logs, generic denials, rate limits |
| Audit gaps | Central helper invoked in every state-changing service; test audit coverage |
| Scope creep | P0 first; P1 items documented as follow-on; explicit demo scenarios |
| Demo data unrealistic | Deterministic synthetic seed with every required exception scenario |

## 11. What is left to the builder

- Exact component decomposition and styling details within the design direction.
- Whether to add a lightweight component test setup; Playwright is preferred for flow evidence.
- Database migration tooling beyond prototype `create_all` is a production follow-on.
- Any P1/P2 PRD items not listed in the plan are out of scope for this prototype.

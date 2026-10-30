# APAAR-SDMV Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working, demo-ready APAAR student enrolment governance and controlled-verification platform covering the PRD's MVP acceptance criteria.

**Architecture:** Monorepo with a FastAPI/SQLAlchemy API backed by PostgreSQL and a Next.js 16 role-based portal. The API owns validation, duplicate/capacity rules, workflow, consent tokens, audit, and mock adapters. The web app is a typed client with separate institution, AICTE, student, and public verifier surfaces.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, PyJWT, Argon2, cryptography; Next.js 16, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Recharts, Radix UI, lucide-react, qrcode.react; PostgreSQL 16; pytest; Docker Compose; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-apaar-sdmv-design.md` (source: `APAAR_Student_Data_Platform_PRD.md`)

## Global Constraints

- All data is synthetic. Every UI page shows `Synthetic demo data · Mock integrations`.
- Mock APAAR results must carry `mock: true` and be visually labelled `Mock/sandbox`. Never present a mock result as live APAAR/ABC/DigiLocker/NAD verification.
- APAAR ID is exactly 12 ASCII digits for format validation. Format validity is never identity authenticity.
- Raw APAAR IDs must never appear in logs, audit metadata, URLs, analytics, list views, or exports. Store Fernet ciphertext + HMAC lookup token; display last 4 digits only.
- APAAR IDs are never used as passwords or auth secrets.
- Every institution-owned object query must include a server-side institution-scope check. AICTE roles require the named role; institution roles cannot cross tenants.
- Nodal attestation is required before batch submission. Only `INSTITUTION_NODAL_OFFICER` may attest/submit. AICTE reviewers cannot approve their own institution (no institution membership).
- Blocking validation errors prevent clean submission; warnings/high-severity findings remain visible.
- Duplicate matches create review cases; they never auto-cancel, auto-merge, or label fraud.
- Capacity uses `institution + campus + programme + academic year + approval snapshot + seat classification`; regular and supernumerary are separate; NRI/OCI/FN remain distinct attributes.
- Every material action writes an append-only audit event with actor, role, action, resource, timestamp, reason/metadata. No audit update/delete API.
- Verification tokens are opaque, hashed at rest, expiring, revocable; every success/denial is logged. Expired/revoked tokens return a generic 410.
- Frontend must pass `npm run typecheck` and `npm run build`. Backend must pass `uv run pytest` and `uv run ruff check`.
- API responses use camelCase; DB columns use snake_case. Enums use canonical values in the table below.
- Required canonical enums:
  - Batch: `DRAFT`, `VALIDATING`, `VALIDATION_FAILED`, `READY_FOR_ATTESTATION`, `SUBMITTED`, `UNDER_AICTE_REVIEW`, `RETURNED_FOR_CORRECTION`, `ACCEPTED`, `REJECTED`.
  - Row: `PENDING`, `VALID`, `WARNING`, `ERROR`.
  - Identity: `MISSING`, `MALFORMED`, `FORMAT_VALID`, `PENDING_EXTERNAL_CHECK`, `EXTERNALLY_CONFIRMED`, `EXTERNAL_MISMATCH`, `EXTERNAL_UNAVAILABLE`, `MANUAL_REVIEW`, `CORRECTED`.
  - Capacity: `WITHIN_APPROVED_INTAKE`, `WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY`, `POSSIBLE_EXCESS`, `MISSING_APPROVAL_DATA`, `PENDING_RULE_REVIEW`.
  - Enrollment lifecycle: `PENDING`, `ACTIVE`, `WITHDRAWN`, `TRANSFERRED`, `COMPLETED`, `CANCELLED`, `UNDER_REVIEW`.
  - Seat classification: `APPROVED_REGULAR`, `APPROVED_SUPERNUMERARY`, `OTHER`.
- Every phase ends with: tests green, `git add -A`, descriptive commit, `git push origin main`.

## Review Focus

- **Cross-tenant object access:** an institution role requesting another institution's enrollment, batch, case, export, or student record must receive 403 (or a safe 404) and a security audit event; a UI filter is not authorization.
- **Mock vs verified confusion:** a mock `SUCCESS`, a format-valid APAAR, an accepted institution record, and credential verification must remain visually and semantically distinct everywhere.
- **Duplicate false positives:** same APAAR across institutions with non-overlapping dates (valid transfer) must create a reviewable case, not an automatic fraud label or deletion; the case must show dates and resolution codes.
- **Capacity double counting:** a resubmitted/corrected batch must not count the same enrollment twice; supernumerary capacity must be added only with a valid allocation/reference.
- **Token lifecycle:** expired, revoked, malformed, and replayed tokens must disclose nothing; attempts must be logged; tokens must not appear in logs or URLs beyond the public link path.
- **CSV hostile input:** duplicate headers, formula-leading values, oversized files, >10,000 rows, invalid encodings, and missing columns must fail safely with actionable errors.
- **Correction history:** editing an accepted record or resubmitting a returned batch must preserve prior versions and re-run validation/audit.
- **Report leakage:** analyst exports must contain aggregate-only data; institution exports must be scoped; small groups must be suppressed where required; exports are audited.
- **State-machine illegality:** accepting a DRAFT batch, submitting without attestation, re-deciding an accepted batch, or resolving a closed case must be rejected with a clear conflict.
- **Sensitive data in logs/audit:** raw APAAR values, passwords, token values, and full student records must not enter application logs, audit metadata, or error traces.

---

## Phase 1 — Foundation & Access

Deliverable: a running API + web shell where seeded users sign in, see role-appropriate navigation, and can only access their own institution scope. CI and Docker exist.

### Task 1: Monorepo foundation, schema, and health checks

**Files:**
- Create: `.gitignore`, `.env.example`, `README.md`, `Makefile`, `docker-compose.yml`
- Create: `.github/workflows/ci.yml`
- Create: `apps/api/pyproject.toml`, `apps/api/Dockerfile`, `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`, `apps/api/app/config.py`, `apps/api/app/db.py`, `apps/api/app/errors.py`
- Create: `apps/api/app/models/__init__.py`, `models/base.py`, `models/master.py`, `models/identity.py`, `models/enrollment.py`, `models/batch.py`, `models/review.py`, `models/verification.py`, `models/ops.py`
- Create: `apps/api/tests/conftest.py`, `apps/api/tests/test_health.py`, `apps/api/tests/test_models.py`
- Create: `apps/web/package.json`, `package-lock.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`, `eslint.config.mjs`, `Dockerfile`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`

**Interfaces:**
- Produces: `app.main.create_app() -> FastAPI`; `GET /api/v1/health` → `{status:"ok", version:"0.1.0"}`.
- Produces: `Base` declarative class and every model named in the design doc §5.2 with fields/enums listed there and in the design §5.2 invariants.
- Produces: `Settings` with `database_url`, `jwt_secret`, `apaar_encryption_key`, `apaar_lookup_key`, `receipt_signing_key`, `env`, `cors_origins`; dev defaults allowed only when `env != "production"`.
- Produces: `get_db()` FastAPI dependency; SQLite test override via `DATABASE_URL`.
- Produces: `AppError(status_code, code, message, details=None)` and handler returning `{error:{code,message,details},traceId}`.
- Produces: root scripts `make dev`, `make test`, `make seed`, `make build`.

- [ ] **Step 1: Write failing tests**

```python
def test_health_returns_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_all_core_tables_create(db):
    inspector = inspect(db.get_bind())
    expected = {"institutions","campuses","programmes","approval_snapshots","intake_allocations",
      "users","organization_memberships","student_identities","student_enrollments","enrollment_versions",
      "submission_batches","submission_rows","validation_runs","validation_findings","duplicate_cases",
      "identity_verifications","consent_grants","verification_requests","verification_receipts",
      "verification_attempts","audit_events","notifications","report_exports","integration_clients"}
    assert expected <= set(inspector.get_table_names())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_health.py tests/test_models.py -v`  
Expected: FAIL (no app/models).

- [ ] **Step 3: Implement foundation and models**

Use SQLAlchemy 2 `Mapped`/`mapped_column`, UUID string PKs, UTC timestamps. Use `SAEnum(..., native_enum=False, values_callable=...)` or `String` with Python enums. `create_all` on startup only outside tests; tests create/drop per test. Add `GET /api/v1/health`, request trace ID, CORS from settings, and baseline security headers. Create Dockerfiles and compose services `db`, `api`, `web`; Postgres 16; web depends on API. CI installs uv + Node 22, runs API tests with SQLite and `npm ci && npm run build` in `apps/web`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/api && uv run pytest tests/test_health.py tests/test_models.py -v`; `cd apps/web && npm ci && npm run build`  
Expected: PASS; Next.js production build completes.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: scaffold APAAR-SDMV monorepo and data model"
```

### Task 2: Authentication, RBAC, tenant scoping, audit, and core seed

**Files:**
- Create: `apps/api/app/security.py`, `apps/api/app/deps.py`, `apps/api/app/audit.py`, `apps/api/app/constants.py`
- Create: `apps/api/app/schemas/__init__.py`, `schemas/common.py`, `schemas/auth.py`, `schemas/users.py`
- Create: `apps/api/app/routers/__init__.py`, `routers/auth.py`, `routers/users.py`
- Create: `apps/api/app/seed.py`
- Modify: `apps/api/app/main.py`, `apps/api/app/config.py`
- Create: `apps/api/tests/test_auth.py`, `apps/api/tests/test_tenant_scope.py`, `apps/api/tests/factories.py`

**Interfaces:**
- Produces: `hash_password(str)`, `verify_password(str,str)`, `create_access_token(user) -> (token, expires_in)`, `decode_token(str) -> dict`.
- Produces: `get_current_user`, `require_roles(*roles)`, `get_institution_scope(user) -> str | None`, `assert_institution_access(db, user, institution_id, request=None)`; raises `AppError(403, "FORBIDDEN")` and writes `SECURITY_ACCESS_DENIED` audit on cross-tenant attempts.
- Produces: `record_audit(db, *, actor, action, resource_type, resource_ref, reason=None, metadata=None, request=None)`.
- Produces: `POST /api/v1/auth/login` body `{email,password}` → `{accessToken, expiresIn, user}`; `GET /api/v1/auth/me` → `UserContext`.
- Produces: `UserContext = {id,email,fullName,roles,primaryRole,institutionId,institutionName,studentIdentityId,mfaEnabled}`.
- Produces: `GET /api/v1/institutions/me/users` and `POST /api/v1/institutions/me/users/invitations` (institution admin only; invitation returns one-time demo temp password, audited).
- Produces: seed accounts and organizations from design §4; command `uv run python -m app.seed --reset`.
- Produces: factories `make_user(role, institution=None)`, `auth_headers(client, email)`.

- [ ] **Step 1: Write failing tests**

```python
def test_login_and_me(client, seeded):
    r = client.post("/api/v1/auth/login", json={"email":"operator@demo-ait.edu","password":"Demo@1234"})
    assert r.status_code == 200
    token = r.json()["accessToken"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert "INSTITUTION_OPERATOR" in me.json()["roles"]

def test_bad_password_is_generic(client, seeded):
    r = client.post("/api/v1/auth/login", json={"email":"operator@demo-ait.edu","password":"wrong"})
    assert r.status_code == 401
    assert "password" not in r.json()["error"]["message"].lower()

def test_institution_user_list_is_admin_scoped(client, seeded):
    headers = auth_headers(client, "admin@demo-ait.edu")
    r = client.get("/api/v1/institutions/me/users", headers=headers)
    assert r.status_code == 200
    assert all(u["institutionId"] == "inst_ait" for u in r.json()["items"])

def test_operator_cannot_list_institution_users(client, seeded):
    headers = auth_headers(client, "operator@demo-ait.edu")
    assert client.get("/api/v1/institutions/me/users", headers=headers).status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_auth.py tests/test_tenant_scope.py -v`  
Expected: FAIL (no routes/deps).

- [ ] **Step 3: Implement auth, RBAC, audit, seed**

Argon2 via `pwdlib[argon2]`; JWT HS256 30 min with `sub`, `roles`, `institutionId`, `jti`; active membership lookup. `require_roles` returns a dependency that checks any membership role. Login audits success/failure with email and IP but never password. Seed 3 institutions, campuses, programmes, approvals/intake for 2025-26 and 2026-27, and users from design §4. Use deterministic IDs (`inst_ait`, `prog_ait_cse`, etc.) so later demo data is stable.

- [ ] **Step 4: Run tests and seed smoke**

Run: `cd apps/api && uv run pytest -v`; `uv run python -m app.seed --reset`; `uv run python -c "from app.seed import seed; seed(reset=True)"`  
Expected: PASS; seed prints counts.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add authentication, RBAC, tenant scope, audit and seed users"
```

### Task 3: Web design system, auth flow, and role-based shell

**Files:**
- Create: `apps/web/src/lib/api.ts`, `lib/types.ts`, `lib/auth.tsx`, `lib/utils.ts`, `lib/nav.ts`
- Create: `src/components/ui/button.tsx`, `badge.tsx`, `card.tsx`, `input.tsx`, `select.tsx`, `dialog.tsx`, `tabs.tsx`, `table.tsx`, `skeleton.tsx`, `empty-state.tsx`, `tooltip.tsx`
- Create: `src/components/layout/app-shell.tsx`, `sidebar.tsx`, `topbar.tsx`, `mobile-nav.tsx`, `demo-banner.tsx`, `page-header.tsx`
- Create: `src/components/logo.tsx`, `role-badge.tsx`, `status-badge.tsx`
- Create: `src/app/login/page.tsx`, `src/app/(portal)/layout.tsx`, `src/app/(portal)/page.tsx`
- Modify: `src/app/layout.tsx`, `globals.css`, `next.config.ts`
- Create: `apps/web/.env.example`

**Interfaces:**
- Consumes: Task 2 auth endpoints.
- Produces: `apiFetch<T>(path, {method, body, token, ...})`, `api` helpers, and `ApiError {code,message,status,details}`.
- Produces: `AuthProvider`, `useAuth()` with `user`, `token`, `login(email,password)`, `logout()`, `isLoading`; token in `localStorage` key `apaar_sdmv_token`.
- Produces: `PortalShell` role-aware nav groups. Institution nav: Overview, Students, Batches, Programmes & Intake, Cases, Team. AICTE nav: National Overview, Review Queue, Institutions, Cases, Reports, Audit. Student nav: My Record, Sharing. Verifier nav: Verify a Reference. Admin adds Users when built.
- Produces: `StatusBadge` variant map for every canonical enum; distinct badge families for `identity`, `review`, `capacity`, `severity`, `mock`.
- Produces: design tokens in CSS: ink `#0B1F33`, canvas `#F5F7FA`, surface `#FFFFFF`, primary teal `#0F766E`, accent amber `#B45309`, danger `#B42318`, border `#DDE3EA`; Sora display + Public Sans body via `next/font`.
- Produces: `/login` split layout with 10 demo account chips that fill the form; `/` redirects by role (institution → `/institution`, AICTE roles → `/aicte`, student → `/student`, verifier → `/verifier`).

- [ ] **Step 1: Write failing tests**

```tsx
// src/lib/__tests__/nav.test.ts
import { navForRoles } from "@/lib/nav";
it("institution nav excludes AICTE audit", () => {
  const hrefs = navForRoles(["INSTITUTION_OPERATOR"]).map((n) => n.href);
  expect(hrefs).toContain("/institution/batches");
  expect(hrefs).not.toContain("/aicte/audit");
});
```

Add `vitest` + `@testing-library/react` config and run `npm run test -- --run`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/web && npm run test -- --run`  
Expected: FAIL (no nav module).

- [ ] **Step 3: Implement design system, auth, and shell**

Use Tailwind 4 `@theme` tokens. Build accessible primitives (Radix Dialog/Tabs/Tooltip; native select/input). Sidebar dark ink with teal active indicator, demo ribbon above content, topbar with notification bell placeholder and user menu. Placeholder portal pages should read “Module arriving in Phase 2” but render with real shell. Ensure mobile drawer keyboard accessible. Add security headers in `next.config.ts` (`X-Frame-Options`, `Referrer-Policy`, `X-Content-Type-Options`, `Permissions-Policy`). Persist auth and redirect unauthenticated users to `/login`. Do not use a single “Verified” badge anywhere.

- [ ] **Step 4: Verify build and typecheck**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit and push Phase 1**

```bash
git add -A
git commit -m "feat: add role-based web shell and sign-in experience"
git push origin main
```

---

## Phase 2 — Master Data & Ingestion

Deliverable: AICTE master data and approved intake are real; institutions can add students, upload CSV batches, see row-level validation, review duplicates/capacity, attest, and submit.

### Task 4: Master-data APIs, APAAR protections, mock adapter, and rich seed

**Files:**
- Create: `apps/api/app/schemas/master.py`, `schemas/identity.py`
- Create: `apps/api/app/routers/institutions.py`, `routers/programmes.py`
- Create: `apps/api/app/adapters/__init__.py`, `adapters/apaar.py`
- Create: `apps/api/app/services/apaar.py`, `services/capacity.py`
- Modify: `apps/api/app/main.py`, `app/seed.py`
- Create: `apps/api/tests/test_master_data.py`, `tests/test_apaar.py`, `tests/test_capacity.py`
- Create: `data/demo/template.csv`, `data/demo/mixed_errors.csv`, `data/demo/valid_batch.csv`

**Interfaces:**
- Produces: `encrypt_apaar(raw: str) -> str`; `apaar_lookup_token(raw: str) -> str`; `mask_apaar(raw: str | None) -> str` returning `••••••••1234`.
- Produces: `upsert_student_identity(db, raw_apaar, status) -> StudentIdentity`; malformed/absent handled without encryption.
- Produces: `ApaarVerificationProvider.verify(identifier, purpose, consent_context) -> ApaarVerificationResult{outcome,reference,checked_at,adapter_version,mock}` with outcomes `SUCCESS|NOT_FOUND|MISMATCH|UNAVAILABLE|TIMEOUT|UNAUTHORIZED|UNSUPPORTED`.
- Produces: `MockApaarProvider`; identifiers ending `99` → MISMATCH, ending `88` → UNAVAILABLE, otherwise SUCCESS; always `mock=True`, version `mock-1.0`.
- Produces: `calculate_capacity(db, programme_id, academic_year) -> CapacityResult{allocations, reported, projected, status, evidence}` using current submitted/accepted enrollments only.
- Produces endpoints:
  - `GET /institutions/me` + `/campuses` + `/programmes` + `/intake?academicYear=`
  - `GET /institutions?search=&page=`, `GET /institutions/{id}`, `POST /institutions`, `POST /institutions/{id}/campuses`
  - `POST /campuses/{id}/programmes`, `GET /programmes?institutionId=&academicYear=`
  - `POST /programmes/{id}/intake-snapshots`, `GET /intake?programmeId=&academicYear=`, `PATCH /intake-allocations/{id}`
- Produces: seeded 3 institutions, 5 campuses, 8 programmes, 2025-26 + 2026-27 intake snapshots with regular/supernumerary allocations, ~90 enrollments across institutions (`is_current=true`, version 1 snapshots), and stable demo identities.

- [ ] **Step 1: Write failing tests**

```python
def test_masking_and_encryption_roundtrip(db):
    raw = "123456789012"
    ident = upsert_student_identity(db, raw, "FORMAT_VALID")
    assert ident.apaar_ciphertext != raw
    assert ident.apaar_lookup_token == apaar_lookup_token(raw)
    assert mask_apaar(raw) == "••••••••9012"

def test_mock_provider_outcomes():
    assert MockApaarProvider().verify("111111111111", "enrolment", {}).outcome == "SUCCESS"
    assert MockApaarProvider().verify("111111111199", "enrolment", {}).outcome == "MISMATCH"
    assert MockApaarProvider().verify("111111111188", "enrolment", {}).outcome == "UNAVAILABLE"

def test_institution_cannot_edit_intake(client, seeded):
    headers = auth_headers(client, "admin@demo-ait.edu")
    r = client.patch("/api/v1/intake-allocations/alloc_ait_cse_regular", json={"approvedCount": 500}, headers=headers)
    assert r.status_code == 403

def test_capacity_supernumerary_separate(client, seeded, reviewer_headers):
    data = client.get("/api/v1/intake?programmeId=prog_ait_cse&academicYear=2026-27", headers=reviewer_headers).json()
    assert data["allocations"]["APPROVED_REGULAR"] >= 1
    assert data["allocations"]["APPROVED_SUPERNUMERARY"] >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_master_data.py tests/test_apaar.py tests/test_capacity.py -v`  
Expected: FAIL.

- [ ] **Step 3: Implement master data, APAAR service, adapter, capacity, seed**

Use `cryptography.fernet.Fernet` with a dev key derived from settings; HMAC-SHA256 lookup. Institution users may only read their institution; AICTE supervisor/system admin may create master data; intake allocations are immutable to institutions. `POST /programmes/{id}/intake-snapshots` creates a new version and supersedes older snapshots with a reason + audit. Seed synthetic names and IDs; do not use real institutions. Seed enrollments directly via models plus `EnrollmentVersion` snapshots; include at least: one same-institution duplicate, one cross-institution overlapping pair, one non-overlapping transfer pair, one malformed/missing APAAR, one supernumerary-with-reference, one supernumerary-without-reference, and one over-intake programme. Keep raw APAAR values in seed constants but never print them.

- [ ] **Step 4: Run tests and seed**

Run: `cd apps/api && uv run pytest -v`; `uv run python -m app.seed --reset`  
Expected: PASS; seed count summary; DB contains ~90 current enrollments.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add master data, APAAR protections, mock adapter and demo seed"
```

### Task 5: Enrolment and CSV batch pipeline with validation, duplicates, capacity, and workflow

**Files:**
- Create: `apps/api/app/schemas/enrollment.py`, `schemas/batch.py`, `schemas/case.py`
- Create: `apps/api/app/routers/enrollments.py`, `routers/batches.py`, `routers/cases.py`
- Create: `apps/api/app/services/csv_import.py`, `services/validation.py`, `services/duplicates.py`, `services/enrollment.py`, `services/notifications.py`, `services/storage.py`
- Create: `apps/api/app/adapters/notifications.py`
- Modify: `app/main.py`, `app/seed.py`
- Create: `apps/api/tests/test_enrollments.py`, `test_batch_upload.py`, `test_validation.py`, `test_batch_workflow.py`, `test_duplicates.py`
- Create: `data/demo/batch_valid.csv`, `batch_mixed.csv` (same shape as template)

**Interfaces:**
- Consumes: Task 4 identity, capacity, adapter, master data.
- Produces: `parse_csv(content: bytes) -> ParsedCsv{headers, rows, errors}` with required header set: `institution_student_id,apaar_id,student_name,programme_code,campus_code,academic_year,admission_date,exit_date,enrollment_status,seat_classification,admission_category,nri_status,oci_status,foreign_national_status,approval_reference`; optional `date_of_birth,gender`.
- Produces: `run_validation(db, batch, actor) -> ValidationRun`; sets batch status `READY_FOR_ATTESTATION` if no row is `ERROR`, else `VALIDATION_FAILED`; persists findings with rule IDs; creates/updates duplicate cases idempotently.
- Produces: `validate_apaar_format(value) -> {"status": "MISSING"|"MALFORMED"|"FORMAT_VALID", "message": ...}`; exactly 12 digits.
- Produces: `create_case_for_match(...) -> DuplicateCase | None` with idempotent `match_group_id`; evidence includes masked identifiers, institution names, admission/exit dates, overlap days, match type, status context.
- Produces: `commit_batch_enrollments(db, batch, actor)` on submit; creates or updates enrollment rows and `EnrollmentVersion` snapshots; bumps batch `version` on resubmission; no double count.
- Produces endpoints:
  - `GET /enrollments?academicYear=&programmeId=&enrollmentStatus=&search=&page=&pageSize=`
  - `POST /enrollments`, `GET /enrollments/{id}` (incl. versions, findings, verification, masked APAAR)
  - `PATCH /enrollments/{id}` (creates new version + audit + revalidation findings; accepted records stay current via new `is_current` row)
  - `POST /enrollments/{id}/verify-identity` (institution admin/operator/nodal for own institution; reviewer for authorized; writes `IdentityVerification`, status, audit)
  - `GET/POST /submission-batches`; `POST /{id}/file`; `POST /{id}/validate`; `GET /{id}`; `GET /{id}/results`; `PATCH /{id}/rows/{rowId}`; `POST /{id}/attest`; `POST /{id}/submit`; `POST /{id}/decision`; `GET /template.csv`; `GET /{id}/receipt`
  - `GET /duplicate-cases?status=&severity=`; `GET /{id}`; `POST /{id}/resolve`; `POST /{id}/request-information`
- Produces: notification fan-out (in-app rows) on validation failure, submission, return, acceptance, rejection, case resolution; mock email delivery rows with status `MOCKED`.

- [ ] **Step 1: Write failing tests**

```python
def test_valid_csv_reaches_ready_for_attestation(client, operator_headers, sample_csv):
    batch = create_batch(client, operator_headers, "2026-27")
    upload = client.post(f"/api/v1/submission-batches/{batch['id']}/file", files={"file": ("valid.csv", sample_csv("batch_valid.csv"), "text/csv")}, headers=operator_headers)
    assert upload.status_code == 200
    run = client.post(f"/api/v1/submission-batches/{batch['id']}/validate", headers=operator_headers)
    assert run.status_code == 200
    detail = client.get(f"/api/v1/submission-batches/{batch['id']}", headers=operator_headers).json()
    assert detail["status"] == "READY_FOR_ATTESTATION"
    assert detail["summary"]["errorRows"] == 0

def test_malformed_apaar_blocks_and_explains(client, operator_headers):
    # mixed CSV contains ABC123, duplicate rows, missing APAAR, cross-institution match
    detail = upload_and_validate(client, operator_headers, "batch_mixed.csv")
    assert detail["status"] == "VALIDATION_FAILED"
    finding = next(f for f in detail["findings"] if f["ruleId"] == "BR-002")
    assert finding["code"] == "APAAR_INVALID_FORMAT"
    assert finding["evidence"]["valueMasked"].endswith("••••")

def test_submit_requires_attestation(client, nodal_headers):
    detail = upload_and_validate(client, nodal_headers, "batch_valid.csv")
    r = client.post(f"/api/v1/submission-batches/{detail['id']}/submit", headers=nodal_headers)
    assert r.status_code == 409

def test_nodal_attest_submit_and_reviewer_accept(client, nodal_headers, reviewer_headers):
    detail = upload_and_validate(client, nodal_headers, "batch_valid.csv")
    client.post(f"/api/v1/submission-batches/{detail['id']}/attest", json={"declaration": True, "attestationName": "Nodal Officer"}, headers=nodal_headers)
    sub = client.post(f"/api/v1/submission-batches/{detail['id']}/submit", headers=nodal_headers)
    assert sub.json()["status"] == "UNDER_AICTE_REVIEW"
    dec = client.post(f"/api/v1/submission-batches/{detail['id']}/decision", json={"decision":"ACCEPT","reason":"Verified batch"}, headers=reviewer_headers)
    assert dec.json()["status"] == "ACCEPTED"
```

Also test: duplicate same institution creates BR-004 high case; cross-institution non-overlap creates case with `TRANSFER_CONTEXT`; capacity excess BR-008; supernumerary without ref BR-009; tenant isolation for batch/enrollment/case; total rows >10,000 rejected; file >5 MB rejected; no raw APAAR in finding/audit JSON; resubmission after return doesn't double count.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_enrollments.py tests/test_batch_upload.py tests/test_validation.py tests/test_batch_workflow.py tests/test_duplicates.py -v`  
Expected: FAIL.

- [ ] **Step 3: Implement pipeline**

Upload stores bytes privately and computes SHA-256 before parsing. Rows persist `raw_data`, parsed values, row status. Validation bulk-prefetches programme/campus maps, existing identities/enrollments, and capacity counts; no per-row queries. Findings use rule IDs/codes: `APAAR_MISSING` (BR-001), `APAAR_INVALID_FORMAT` (BR-002), `DUPLICATE_IN_BATCH` (BR-003), `DUPLICATE_SAME_INSTITUTION` (BR-004), `POSSIBLE_CROSS_INSTITUTION_OVERLAP` (BR-005), `INVALID_DATE_ORDER` (BR-006), `UNMAPPED_PROGRAMME` (BR-007), `POSSIBLE_INTAKE_EXCESS` (BR-008), `SUPERNUMERARY_REFERENCE_REQUIRED` (BR-009), `ATTRIBUTE_POLICY_REVIEW` (BR-010). Commit only error-free or warning rows; all-or-nothing per batch for blocking errors (institution corrects and revalidates). Attestation requires nodal role, `declaration=true`, no blocking errors. Submission requires attestation and no errors; sets `SUBMITTED` then `UNDER_AICTE_REVIEW`, creates receipt payload (batch id, checksum, counts, actor, timestamp, signature HMAC). Decision endpoint applies legal transitions only; `RETURN` sets rows editable and notifies institution; resubmission increments batch version and replaces current enrollment versions without duplicate counts. All state changes audit.

- [ ] **Step 4: Run tests**

Run: `cd apps/api && uv run pytest -v`  
Expected: PASS (all backend suites).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add enrollment ingestion, validation, duplicate cases and batch workflow"
```

### Task 6: Institution dashboard, programmes/intake, and student surfaces

**Files:**
- Create: `src/app/(portal)/institution/page.tsx`
- Create: `src/app/(portal)/institution/programmes/page.tsx`
- Create: `src/app/(portal)/institution/students/page.tsx`
- Create: `src/app/(portal)/institution/students/[id]/page.tsx`
- Create: `src/app/(portal)/institution/students/new/page.tsx`
- Create: `src/app/(portal)/institution/layout.tsx` (role guard)
- Create: `src/components/institution/kpi-grid.tsx`, `programme-table.tsx`, `student-form.tsx`, `student-table.tsx`, `identity-status.tsx`, `capacity-bar.tsx`, `enrollment-timeline.tsx`
- Create: `src/components/charts/{bar-chart,donut-chart,area-chart}.tsx`
- Create: `src/hooks/use-dashboard.ts`, `use-master-data.ts`, `use-students.ts`
- Create: `src/app/(portal)/institution/programmes/loading.tsx`, `students/loading.tsx`
- Modify: `src/lib/types.ts`, `api.ts`, `nav.ts`
- Create: `src/components/institution/__tests__/identity-status.test.tsx`

**Interfaces:**
- Consumes: `GET /dashboard/institution`, `/institutions/me`, `/programmes`, `/intake`, `/enrollments`, `/enrollments/{id}`, `POST/PATCH /enrollments`, `/verify-identity`.
- Produces: hooks with TanStack Query keys `["institution-dashboard", academicYear]`, `["students", filters]`, `["student", id]`; mutations invalidate relevant keys.
- Produces components: `KpiCard{label,value,hint,tone,icon}`, `CapacityBar{approved,reported,supernumerary,status}`, `IdentityStatus{status,mock?,verifiedAt?}` with distinct chips.
- Produces: student list with filters (year, programme, status, identity, search), pagination, masked APAAR, flag counts; detail with summary, attributes, verification action (mock-labelled), version history, audit timeline.
- Produces: new-student form validated with zod/react-hook-form; fields per CSV contract; a “Synthetic data” notice; success redirect to detail.
- Produces: programmes page with campus filters, approved regular/supernumerary columns, reported counts, capacity state; read-only banner for institution users.

- [ ] **Step 1: Write failing tests**

```tsx
it("does not label a format-valid identity as verified", () => {
  render(<IdentityStatus status="FORMAT_VALID" />);
  expect(screen.getByText(/format valid/i)).toBeInTheDocument();
  expect(screen.queryByText(/^verified$/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/web && npm run test -- --run src/components/institution/__tests__/identity-status.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement institution surfaces**

Dashboard: 6 KPI cards (approved intake, reported enrollment, active, APAAR gaps, unresolved cases, pending batches), capacity-by-programme table, identity-status donut, enrollment-status bars, recent batch timeline, actionable alert list. Programmes/intake read-only. Student list/detail/new. No entity may reveal raw APAAR; show “Last 4 only” helper text. Use skeletons, empty states, error alerts. All action buttons respect role (operator/admin can create; nodal sees batch actions later). Include page-level academic-year selector persisted in URL query.

- [ ] **Step 4: Verify**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add institution dashboard, programme and student experience"
```

### Task 7: Institution batch wizard, results, attestation, and case response UI

**Files:**
- Create: `src/app/(portal)/institution/batches/page.tsx`, `batches/new/page.tsx`, `batches/[id]/page.tsx`
- Create: `src/app/(portal)/institution/cases/page.tsx`, `cases/[id]/page.tsx`
- Create: `src/app/(portal)/institution/team/page.tsx`
- Create: `src/components/batches/{upload-wizard,file-dropzone,validation-summary,row-results-table,row-edit-dialog,batch-timeline,attestation-dialog,receipt-dialog,status-stepper}.tsx`
- Create: `src/components/cases/{case-table,case-evidence,resolution-dialog}.tsx`
- Create: `src/hooks/{use-batches,use-cases,use-team}.ts`
- Modify: `src/lib/types.ts`, `api.ts`
- Create: `src/components/batches/__tests__/validation-summary.test.tsx`

**Interfaces:**
- Consumes: batch/case/user endpoints from Task 5.
- Produces: 4-step wizard — select year/campus → upload CSV or “Use bundled sample” → validate/row results → attest & submit (nodal only). Show checksum, uploader, timestamp, file name.
- Produces: row results table with severity/rule/field/message/action, filters, inline edit for `RETURNED_FOR_CORRECTION` rows, revalidate button, downloadable error CSV (client-generated from results, audited for student-level exports).
- Produces: batch detail with status stepper, findings, timeline, attestation dialog (name + declaration checkbox), submit confirmation, submission receipt download (JSON), AICTE decision banner.
- Produces: cases list with severity/status filters and institution scope; detail evidence cards, date-overlap visualization, resolve-as-transfer/concurrent/data-error dialog, request-information message.
- Produces: team page listing users, roles, status; invite dialog for institution admin with returned one-time demo password and copy button.

- [ ] **Step 1: Write failing tests**

```tsx
it("disables attestation until the declaration is accepted", () => {
  render(<AttestationDialog batch={{ status: "READY_FOR_ATTESTATION", attestedAt: null }} canAttest />);
  fireEvent.click(screen.getByRole("button", { name: /attest and submit/i }));
  expect(screen.getByRole("button", { name: /confirm attestation/i })).toBeDisabled();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/web && npm run test -- --run src/components/batches/__tests__/validation-summary.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement batch and case surfaces**

Wizard preserves batch id between steps; upload accepts `.csv` only, enforces 5 MB client-side, shows progress; row errors are actionable and never hidden behind a single toast. Attestation only visible to nodal officer; submit disabled until attested and zero blocking errors. For returned batches, editing a row calls PATCH then revalidate; resubmit creates a new batch version and preserves timeline. Show mock APAAR notices. Case resolution reasons are recorded and displayed. All student-level export actions show a confirmation that the action is audited. Add team management.

- [ ] **Step 4: Verify**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit and push Phase 2**

```bash
git add -A
git commit -m "feat: add batch validation, attestation and case response experience"
git push origin main
```

---

## Phase 3 — AICTE Workflow & Analytics

Deliverable: AICTE reviewers can work a queue, decide batches, resolve cases, and see national dashboards; analysts export aggregates; auditors inspect the trail.

### Task 8: Review, dashboards, reports, notifications, audit, and AICTE master-data APIs

**Files:**
- Create: `apps/api/app/schemas/review.py`, `schemas/dashboard.py`, `schemas/report.py`, `schemas/ops.py`
- Create: `apps/api/app/routers/review.py`, `routers/dashboards.py`, `routers/reports.py`, `routers/notifications.py`, `routers/audit.py`
- Create: `apps/api/app/services/dashboards.py`, `services/reports.py`, `services/ops.py`
- Modify: `app/main.py`, `app/seed.py`
- Create: `apps/api/tests/test_review.py`, `test_dashboards.py`, `test_reports.py`, `test_notifications_audit.py`

**Interfaces:**
- Produces: `GET /review/queue?status=&institutionId=&severity=&page=` (AICTE reviewer/supervisor); `GET /review/summary`.
- Produces: `POST /submission-batches/{id}/decision` enhanced with reviewer assignment, reason codes (`DATA_QUALITY`, `INTAKE_EXCEPTION`, `IDENTITY_REVIEW`, `POLICY`, `OTHER`), decision history; prevents illegal transitions; supervisor can reassign.
- Produces: `GET /dashboard/institution` (institution roles) and `GET /dashboard/national` (AICTE roles) with shapes from design §5.3; filters by academic year, institution type, state.
- Produces: report services:
  - `GET /reports/enrolment?academicYear=&institutionId=&programmeId=&groupBy=programme|institution` → aggregate rows, `generatedAt`, `filters`, `dataFreshness`, `suppressedGroups`.
  - `GET /reports/intake-reconciliation?...` → per programme/campus approved/reported/supernumerary/status/evidence.
  - `GET /reports/data-quality?...` → completeness, APAAR status counts, findings by rule/severity, case counts.
  - `GET /reports/{type}/export.csv` → scoped CSV; analyst aggregate only; institution student-level allowed only for own institution and role admin/operator/nodal; exports audited and formula-injection neutralized.
- Produces: `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`; notification DTO includes event type, title, body, channel, deliveryStatus, resource link, readAt.
- Produces: `GET /audit-events?action=&actorId=&resourceType=&resourceRef=&from=&to=&page=` (auditor/supervisor/system admin); append-only; audit detail has no raw identifiers.
- Produces endpoints for reviewer/admin user directory: `GET /admin/users`, `PATCH /admin/users/{id}/status`, `POST /admin/users/{id}/roles` (system admin only; audited; cannot approve regulatory records).
- Produces: seeded historical batches (accepted, returned, under review), open/resolved cases, notifications, and audit events for a rich national dashboard.

- [ ] **Step 1: Write failing tests**

```python
def test_reviewer_queue_requires_aicte_role(client, operator_headers, reviewer_headers):
    assert client.get("/api/v1/review/queue", headers=operator_headers).status_code == 403
    r = client.get("/api/v1/review/queue", headers=reviewer_headers)
    assert r.status_code == 200
    assert "items" in r.json()

def test_analyst_export_has_no_direct_identifiers(client, analyst_headers):
    r = client.get("/api/v1/reports/enrolment/export.csv?groupBy=institution", headers=analyst_headers)
    assert r.status_code == 200
    assert "student_name" not in r.text.lower()
    assert "apaar" not in r.text.lower()
    assert "text/csv" in r.headers["content-type"]

def test_institution_export_scoped_and_masked(client, operator_headers):
    r = client.get("/api/v1/reports/enrolment/export.csv?groupBy=programme", headers=operator_headers)
    assert r.status_code == 200
    assert "inst_bie" not in r.text.lower()
```

Also test audit filters and 403, notification read state scoped to recipient, illegal decision transition 409, report suppression threshold (<5 groups), CSV formula neutralization.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_review.py tests/test_dashboards.py tests/test_reports.py tests/test_notifications_audit.py -v`  
Expected: FAIL.

- [ ] **Step 3: Implement review/analytics/ops services**

Dashboard aggregates use SQL `group_by`; no per-row Python loops over the full dataset. National KPIs: institutions reporting, total current enrollments, submissions by status, possible excess programmes, missing/malformed APAAR, open cases, review turnaround. Institution KPIs: approved/reported, active, identity gaps, unresolved cases, pending batches, programme capacity rows, identifier/status breakdowns, recent batches. Reports return only fields allowed by role; `AICTE_ANALYST` always aggregate and never names/APAAR; institutions only own data. Suppress aggregate rows with `count < 5` for analyst (mark `suppressed: true`). CSV exports escape `= + - @` leading cells. Every export writes a `ReportExport` + audit event. Notifications are fan-out by role/institution with mock email delivery. Audit reads are read-only and cannot expose metadata keys `apaar`, `password`, `token`.

- [ ] **Step 4: Run tests**

Run: `cd apps/api && uv run pytest -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add AICTE review, dashboards, reports, notifications and audit APIs"
```

### Task 9: AICTE national dashboard and review workspace

**Files:**
- Create: `src/app/(portal)/aicte/page.tsx`, `aicte/layout.tsx`, `aicte/review/page.tsx`, `aicte/review/[id]/page.tsx`
- Create: `src/app/(portal)/aicte/institutions/page.tsx` (list shell; detail in Task 10)
- Create: `src/components/aicte/{national-kpi-grid,intake-vs-enrollment,quality-trend,review-queue-table,batch-evidence,batch-decision-panel,review-timeline,risk-callout}.tsx`
- Create: `src/hooks/{use-national-dashboard,use-review}.ts`
- Modify: `src/lib/types.ts`, `api.ts`, `nav.ts`
- Create: `src/components/aicte/__tests__/decision-panel.test.tsx`

**Interfaces:**
- Consumes: Task 8 review/dashboard APIs.
- Produces: national dashboard with 8 KPIs, intake vs reported chart, institution-type distribution, quality trend, review backlog, possible-excess list, cross-institution case queue, institution reporting table with drill-down links, academic-year/state filters.
- Produces: review queue with status tabs (`UNDER_AICTE_REVIEW`, `RETURNED_FOR_CORRECTION`, `ACCEPTED`, `REJECTED`), search, institution/severity filters, age/SLA indicator, assignment chip.
- Produces: batch review page with summary header, validation findings by severity, row-level evidence (masked), capacity evidence, duplicate links, decision panel with `ACCEPT`, `RETURN_FOR_CORRECTION`, `REJECT`, reason code, free-text reason, confirmation; illegal actions disabled with explanation.
- Produces: reviewer sees “Decision recorded by … at …” and timeline; no edit of student fields from AICTE side.

- [ ] **Step 1: Write failing test**

```tsx
it("requires a reason before returning a batch", () => {
  render(<BatchDecisionPanel batch={underReviewBatch} role="AICTE_REVIEWER" />);
  fireEvent.click(screen.getByRole("button", { name: /return for correction/i }));
  expect(screen.getByRole("button", { name: /confirm return/i })).toBeDisabled();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npm run test -- --run src/components/aicte/__tests__/decision-panel.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement AICTE dashboard/review UI**

Data-dense but legible layout. Charts use teal/amber/red semantics; legends and accessible labels. Review decisions require reason and show consequence copy (“Institution will be notified; records remain non-accepted until resubmission”). Summaries distinguish `APAAR format valid` from `External check: mock confirmed`. No bulk accept in MVP. Include empty/loading/error states and responsive tables.

- [ ] **Step 4: Verify**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add AICTE national dashboard and review workspace"
```

### Task 10: AICTE master data, cases, reports, audit, and notifications UI

**Files:**
- Create: `src/app/(portal)/aicte/institutions/[id]/page.tsx`
- Create: `src/app/(portal)/aicte/intake/page.tsx`
- Create: `src/app/(portal)/aicte/cases/page.tsx`, `aicte/cases/[id]/page.tsx`
- Create: `src/app/(portal)/aicte/reports/page.tsx`
- Create: `src/app/(portal)/aicte/audit/page.tsx`
- Create: `src/app/(portal)/notifications/page.tsx`
- Create: `src/components/aicte/{institution-form,campus-form,programme-form,intake-form,intake-table,report-table,export-button,audit-table,audit-detail}.tsx`
- Create: `src/components/notifications/notification-list.tsx`
- Create: `src/hooks/{use-admin-data,use-audit,use-notifications}.ts`
- Modify: `src/lib/types.ts`, `api.ts`, `nav.ts`, `topbar.tsx`
- Create: `src/components/aicte/__tests__/intake-form.test.tsx`

**Interfaces:**
- Consumes: Task 4 master data, Task 8 cases/reports/audit/notifications.
- Produces: institution directory with search, type/state filters, reporting status; detail tabs (profile, campuses, programmes, intake history); create institution/campus/programme dialogs; intake snapshot wizard with version, approval reference, regular + supernumerary allocations and authorization reference; audit reason required.
- Produces: cases workspace with cross-institution evidence, request-information action, resolution dialog (`VALID_TRANSFER`, `PERMITTED_CONCURRENT_ENROLMENT`, `DATA_ERROR`, `UNRESOLVED`, `POLICY_BREACH` — only with supervisor confirmation), history.
- Produces: reports page with tabs Enrolment / Intake reconciliation / Data quality, filters, generated-at/freshness note, suppression callout, CSV download with audit warning.
- Produces: audit page filters (action, actor, resource, date), table, detail drawer with masked metadata; no edit controls.
- Produces: notifications page and topbar unread count; mark one/all read; role-scoped.

- [ ] **Step 1: Write failing test**

```tsx
it("shows supernumerary separately from regular intake", () => {
  render(<IntakeForm programme={programme} />);
  expect(screen.getByLabelText(/regular approved seats/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/authorized supernumerary seats/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/authorization reference/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npm run test -- --run src/components/aicte/__tests__/intake-form.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement AICTE admin/reporting surfaces**

Master-data mutations only for `AICTE_SUPERVISOR` and `SYSTEM_ADMIN`; reviewer sees read-only. Intake edit creates a new snapshot version, never mutates history. Reports respect role: analyst sees aggregate-only and suppression; reviewer/supervisor can drill to institution aggregates but not student rows. Audit page read-only for `AUDITOR`/supervisor/system admin. Notifications use relative timestamps and safe copy without student identifiers. Ensure dialogs are keyboard accessible and forms validate inline.

- [ ] **Step 4: Verify**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit and push Phase 3**

```bash
git add -A
git commit -m "feat: add AICTE master data, cases, reports, audit and notifications UI"
git push origin main
```

---

## Phase 4 — Controlled Verification

Deliverable: A student can authorize a purpose-bound share; a verifier sees only the granted claims through an expiring QR/link; revocation and expiry fail closed; every attempt is audited.

### Task 11: Consent, verification tokens, signed receipts, and public resolution APIs

**Files:**
- Create: `apps/api/app/schemas/verification.py`
- Create: `apps/api/app/routers/verification.py`, `routers/student.py`
- Create: `apps/api/app/services/verification.py`
- Modify: `app/main.py`, `app/seed.py`, `app/config.py`
- Create: `apps/api/tests/test_verification.py`, `test_public_verify.py`

**Interfaces:**
- Consumes: StudentIdentity/Enrollment, audit, storage.
- Produces: `create_verification_request(db, student_user, payload) -> VerificationRequest` status `PENDING_AUTHORIZATION`; fields recipientName, recipientOrg, recipientEmail, purpose, requestedClaims (allow-listed), legalBasis, expiresInHours (1–168).
- Produces: `authorize_request(db, request, student_user) -> {token, verifyUrl, expiresAt, receipt}`; creates `ConsentGrant` (specific recipient/purpose/fields/notice version) and opaque token; stores SHA-256 hash + JTI; sets `AUTHORIZED`; audit.
- Produces: `resolve_public_token(db, token, request_meta) -> VerificationDisclosure`; validates hash, status, expiry, revocation, optional single-use; creates `VerificationAttempt` for success and denial; returns claims with `{key,label,value,source,status,asOf}`; creates `VerificationReceipt` HMAC-SHA256 over canonical JSON; sets `VIEWED`/`EXPIRED`; audit.
- Produces: `revoke_request(db, request, actor, reason)`; authorizes student or supervisor; sets `REVOKED`, revokes consent, audit.
- Produces endpoints:
  - `POST /verification-requests`, `GET /verification-requests?scope=mine|all&status=`, `GET /verification-requests/{id}`
  - `POST /verification-requests/{id}/authorize`, `POST /verification-requests/{id}/revoke`
  - `POST /verification-requests/{id}/issue-link` (alias of authorize for authorized requests, returns fresh link only if not revoked)
  - `GET /public/verify/{token}` (no auth; rate-limited; returns `{valid:true, claims, receipt, expiresAt, demoNotice}` or `{valid:false, reason}` with 410 for denied)
  - `GET /students/me` (student) → masked identity, own enrollments, active/recent requests/consents.
- Produces seeded active, expired, and revoked verification requests for `student@demo-ait.edu`, plus receipts/attempts.

- [ ] **Step 1: Write failing tests**

```python
def test_student_authorize_and_public_verify(client, student_headers):
    req = client.post("/api/v1/verification-requests", json={
      "recipientName":"Acme HR","recipientOrg":"Acme Demo","recipientEmail":"hr@acme-demo.example",
      "purpose":"Employment screening","requestedClaims":["INSTITUTION","PROGRAMME","ENROLMENT_STATUS"],
      "legalBasis":"CONSENT","expiresInHours":24}, headers=student_headers).json()
    auth = client.post(f"/api/v1/verification-requests/{req['id']}/authorize", headers=student_headers).json()
    pub = client.get(f"/api/v1/public/verify/{auth['token']}")
    assert pub.status_code == 200
    assert {c["key"] for c in pub.json()["claims"]} == {"INSTITUTION","PROGRAMME","ENROLMENT_STATUS"}
    assert "student_name" not in pub.text.lower()
    assert pub.json()["receipt"]["signature"]

def test_expired_and_revoked_tokens_deny_without_disclosure(client, student_headers):
    # create -> authorize -> revoke -> 410; create -> force expire -> 410
    assert client.get(f"/api/v1/public/verify/{revoked_token}").status_code == 410
    assert "programme" not in client.get(f"/api/v1/public/verify/{revoked_token}").text.lower()

def test_verification_attempts_audited(client, student_headers, auditor_headers):
    # success + denial create VerificationAttempt rows and audit events; audit metadata has token hash prefix only
    ...
```

Also test: unauthenticated cannot create; non-student cannot authorize; claims allow-list rejects `STUDENT_NAME`; rate limit returns 429 after N requests; receipt signature verifies with test key.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_verification.py tests/test_public_verify.py -v`  
Expected: FAIL.

- [ ] **Step 3: Implement verification service**

Token: `secrets.token_urlsafe(32)`; store SHA-256 hex; return raw token once. Public route must not require auth but must rate limit by IP (10/min auth, 30/min verify). Claims are built only from the student's current accepted/submitted enrollment; `RECORD_ACCEPTANCE` reflects batch status; `APAAR_EXTERNAL_STATUS` includes `mock:true` when applicable. Receipt canonical JSON: `{requestId, claimsHash, issuedAt, expiresAt, subjectRef, keyId}`; signature = HMAC-SHA256 with settings key; expose algorithm/keyId only. Denials: generic message, 410; log attempt with token hash prefix, IP, UA, reason, but never raw token. Expiry checked server-side. Revocation updates consent and request; any later public resolve denies. Student `GET /students/me` returns only own records. Seed active/expired/revoked examples.

- [ ] **Step 4: Run tests**

Run: `cd apps/api && uv run pytest -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add consent-scoped verification, signed receipts and public resolution"
```

### Task 12: Student sharing portal, QR experience, and public verifier page

**Files:**
- Create: `src/app/(portal)/student/page.tsx`, `student/layout.tsx`
- Create: `src/app/(portal)/student/share/page.tsx`, `student/share/[id]/page.tsx`
- Create: `src/app/(portal)/verifier/page.tsx`
- Create: `src/app/verify/[token]/page.tsx` (public, no portal shell)
- Create: `src/components/student/{record-card,identity-card,share-wizard,share-list,qr-dialog,consent-history}.tsx`
- Create: `src/components/verify/{verification-result,claim-card,receipt-download,denied-state,verified-header}.tsx`
- Create: `src/hooks/{use-student,use-verification}.ts`
- Modify: `src/lib/types.ts`, `api.ts`, `nav.ts`
- Create: `src/components/student/__tests__/share-wizard.test.tsx`

**Interfaces:**
- Consumes: Task 11 student/verification APIs.
- Produces: student dashboard with masked identity, current enrollment, record acceptance state, APAAR format/external status chips, active shares, “Create share” CTA.
- Produces: share wizard (recipient, purpose, claims multi-select, duration 1–168h, legal-basis note, review screen), authorization result with QR code, copy link, expiry countdown, download signed receipt, revoke action with confirmation.
- Produces: share detail/history with statuses (`PENDING_AUTHORIZATION`, `AUTHORIZED`, `VIEWED`, `REVOKED`, `EXPIRED`), field scope, audit trail.
- Produces: public `/verify/[token]` page fetching public API without auth: prominent claim-by-claim source/status labels, demo/mock banner, expiry, signed receipt JSON download, generic denied state for 410; print-friendly CSS.
- Produces: verifier portal shell with a “paste verification reference” box (extracts token from URL) and explanation that verifiers get no search or bulk lookup.

- [ ] **Step 1: Write failing test**

```tsx
it("requires explicit claim selection before authorizing", () => {
  render(<ShareWizard open onOpenChange={() => {}} />);
  expect(screen.getByRole("button", { name: /review authorization/i })).toBeDisabled();
  fireEvent.click(screen.getByLabelText(/programme/i));
  expect(screen.getByRole("button", { name: /review authorization/i })).toBeEnabled();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npm run test -- --run src/components/student/__tests__/share-wizard.test.tsx`  
Expected: FAIL.

- [ ] **Step 3: Implement student and verifier surfaces**

Route guard must allow `/verify/*` unauthenticated; do not wrap public page in portal shell. QR generated locally with `qrcode.react` from the full verify URL; never include claims in the URL. Denied page must not reveal whether a record existed. Claim cards show `Institution-submitted`, `AICTE accepted`, `APAAR format check`, `Mock external check` as separate facts. Share wizard explains what each claim reveals. Revocation confirmation states future access stops. Print stylesheet hides navigation and demo controls. Ensure mobile layout at 390 px.

- [ ] **Step 4: Verify**

Run: `cd apps/web && npm run test -- --run && npm run typecheck && npm run build`  
Expected: PASS.

- [ ] **Step 5: Commit and push Phase 4**

```bash
git add -A
git commit -m "feat: add student consent portal and public verification experience"
git push origin main
```

---

## Phase 5 — Hardening, Demo & Delivery

Deliverable: security/perf/a11y checks, browser evidence, demo script, complete documentation, Docker smoke test, and a reviewed branch.

### Task 13: Security, upload, rate-limit, performance, accessibility, and E2E hardening

**Files:**
- Create: `apps/api/app/middleware.py` (rate limiting, security headers, redacting log filter)
- Modify: `app/main.py`, `app/config.py`, `app/routers/auth.py`, `app/routers/verification.py`, `app/services/csv_import.py`, `app/services/reports.py`
- Create: `apps/api/tests/test_security_hardening.py`, `tests/test_upload_limits.py`, `tests/test_performance.py`
- Create: `apps/web/playwright.config.ts`, `e2e/smoke.spec.ts`, `e2e/institution-batch.spec.ts`, `e2e/verification.spec.ts`
- Create: `scripts/smoke.sh`, `scripts/benchmark_validation.py`
- Create: `docs/accessibility.md`
- Modify: `apps/web/src/app/globals.css`, `next.config.ts` (if a11y/security fixes needed)

**Interfaces:**
- Produces: rate limits — login 10/min/IP, public verify 30/min/IP; 429 with `Retry-After` and safe error body.
- Produces: upload guards — `.csv` extension, `text/csv` or `text/plain`, ≤5 MB, ≤10,000 rows, UTF-8 with BOM tolerated, duplicate/missing headers rejected, formula-leading values neutralized on export.
- Produces: security headers on API + web; CORS restricted to configured origins; no server banner; secret validation fails in production.
- Produces: structured log redaction filter for 12-digit sequences, `Bearer` tokens, password/token fields; test that log records contain no raw APAAR.
- Produces: `scripts/benchmark_validation.py` generating 10,000 rows and printing duration; target <300 s; test with 2,000 rows asserts <60 s in CI.
- Produces: Playwright suites for login → institution dashboard; upload sample → validate → attest → submit; reviewer accept; student authorize → public verify → revoke; expired token denial. Screenshots saved to `docs/evidence/`.
- Produces: accessibility notes and fixes: keyboard nav, focus traps, labels, contrast, reduced motion, table captions.

- [ ] **Step 1: Write failing tests**

```python
def test_upload_rejects_oversize_and_row_limit(client, operator_headers):
    big = b"institution_student_id,apaar_id\n" + b"x,123456789012\n" * 10_001
    r = client.post(f"/api/v1/submission-batches/{batch_id}/file", files={"file": ("big.csv", big, "text/csv")}, headers=operator_headers)
    assert r.status_code == 413

def test_apaar_not_in_logs(caplog, client, operator_headers):
    # trigger validation with a known raw APAAR
    assert "123456789012" not in caplog.text

def test_public_verify_rate_limit(client):
    for _ in range(31):
        r = client.get("/api/v1/public/verify/invalid-token")
    assert r.status_code == 429
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/test_security_hardening.py tests/test_upload_limits.py tests/test_performance.py -v`  
Expected: FAIL.

- [ ] **Step 3: Implement hardening**

Use a small in-process sliding-window limiter keyed by IP+route for the prototype; note Redis-backed production. Add middleware order so trace ID and security headers are present on errors. Validate secrets at startup when `ENV=production`. Redact logs and exception strings; never log request bodies for auth/verification/upload. Optimize validation with bulk maps; add indexes on `(institution_id, academic_year)`, `(batch_id, source_row_number)`, `apaar_lookup_token`, `(programme_id, academic_year)`, `(recipient_user_id, read_at)`. For Playwright, use a seeded local database and start servers via config; skip gracefully if browsers unavailable in CI, but run locally and save screenshots. Add `aria-label`, captions, focus management where audit finds gaps.

- [ ] **Step 4: Run tests, benchmark, e2e**

Run: `cd apps/api && uv run pytest -v`; `uv run python scripts/benchmark_validation.py` (or `uv run python ../../scripts/benchmark_validation.py` from API); `cd apps/web && npm run test -- --run && npm run typecheck && npm run build && npx playwright test`  
Expected: PASS; benchmark prints rows and duration under target; e2e screenshots captured.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "test: harden security, uploads, performance and browser flows"
```

### Task 14: Demo dataset, documentation, Docker smoke, and final review fixes

**Files:**
- Create: `docs/demo-script.md`, `docs/api.md`, `docs/data-dictionary.md`, `docs/deployment.md`, `docs/security.md`, `docs/privacy.md`, `docs/limitations.md`
- Create: `docs/evidence/README.md` + screenshots from Task 13
- Modify: `README.md`, `Makefile`, `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`
- Modify: seed data only if demo script reveals a missing scenario
- Create: `apps/api/tests/test_acceptance.py` (PRD §22 checklist encoded where automatable)

**Interfaces:**
- Produces: README with product summary, screenshots, architecture diagram, features by PRD requirement, quickstart (`docker compose up --build`), local dev, demo accounts, test commands, security/mock disclaimers, known limitations.
- Produces: `docs/demo-script.md` matching PRD §19 step-by-step with exact demo accounts, CSV files, expected outcomes, and fallbacks.
- Produces: API docs (auth, endpoints, error format, roles, pagination), data dictionary (every field, purpose, sensitivity, retention note), deployment runbook (env secrets, migrations note, TLS/OIDC/Redis/S3 production path), security threat model + controls, privacy/DPDP notes, limitations (synthetic data, mock adapters, no live gov APIs).
- Produces: acceptance test mapping each PRD §22 criterion to a passing test or documented manual check.
- Produces: Docker smoke evidence: `docker compose up -d --build`, health checks, seed, login, upload/validate, public verification curl, `docker compose down`; screenshots or command transcript in docs.
- Produces: final whole-branch review findings fixed; deferred minors documented.

- [ ] **Step 1: Write failing acceptance tests**

```python
def test_mvp_acceptance_smoke(client, seeded):
    # institution login, own dashboard, upload valid CSV, validate, attest, submit,
    # reviewer decision, duplicate case exists, expired verification denied, audit exists
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && uv run pytest tests/test_acceptance.py -v`  
Expected: FAIL until missing wiring/docs scenario is complete.

- [ ] **Step 3: Complete demo/docs/Docker and fix gaps**

Ensure `.env.example` contains every var with safe dev values and production warnings. Compose uses healthchecks and starts db → api → web; API seed runs idempotently. Add `make demo` (seed + up) and `make reset`. Verify all 10 accounts can sign in. Generate and check demo CSV downloads. Add screenshots for login, institution dashboard, batch results, AICTE dashboard, review, verification result, denied token. Run `docker compose config` and a full smoke. Update README feature matrix with exact shipped statuses; do not overclaim P1/P2 items.

- [ ] **Step 4: Full verification**

Run:
```bash
cd apps/api && uv run ruff check . && uv run pytest -v
cd ../web && npm run test -- --run && npm run typecheck && npm run build
cd ../.. && docker compose build && docker compose up -d && ./scripts/smoke.sh && docker compose down
```
Expected: all green; smoke prints PASS for health/auth/upload/verify.

- [ ] **Step 5: Commit and push Phase 5**

```bash
git add -A
git commit -m "docs: add demo script, API, data dictionary, security and deployment guides"
git push origin main
```

---

## Self-Review

### Spec coverage

| PRD area | Plan tasks |
|---|---|
| §5 roles/RBAC, tenant isolation | 1, 2, 5, 8, 13 |
| §7.1 institution/campus/programme/intake | 1, 2, 4, 10 |
| §7.2 single entry + CSV staging + states | 1, 5, 7 |
| §7.3 APAAR format vs external verification, mock adapter | 4, 5, 6 |
| §7.4 duplicate/anomaly detection + review | 5, 7, 8, 10 |
| §7.5 intake reconciliation/supernumerary | 4, 5, 6, 8 |
| §7.6 workflow, decisions, correction | 5, 7, 8, 9 |
| §7.7 dashboards/reports/exports | 6, 8, 9, 10 |
| §7.8 authorized verification | 11, 12 |
| §7.9 certificate/QR reference | 11, 12 (verification reference/QR; certificate issuance explicitly out) |
| §7.10 notifications | 5, 8, 10 |
| §7.11 audit/history | 1, 2, 5, 8, 10, 13 |
| §9 business rules | 5, 8, 13 |
| §10 data model/crypto/versioning | 1, 4, 5 |
| §11 API conventions | 1–12 |
| §12 architecture | 1, 13, 14 |
| §13 security/privacy | 4, 11, 13, 14 |
| §14 NFRs | 13 (latency target documented; 10k benchmark), 14 (deployment) |
| §15 UX/status design | 3, 6, 7, 9, 10, 12 |
| §16 KPIs | 8, 9, 10 |
| §17 testing | 13, 14 |
| §18 delivery phases | phases 1–5 |
| §19 demo plan | 14 |
| §22 acceptance criteria | 14 (mapping test) |
| §23 definition of done | Global Constraints + 14 |

### Type consistency checks

- `StudentEnrollment` uses `seatClassification`, `enrollmentStatus`, `recordStatus`; API DTOs use the same camelCase names.
- `IdentityStatus` values in plan match design §5.2.
- Batch/row/capacity enums match Global Constraints.
- `AuthProvider.login` consumes Task 2 `POST /auth/login`; later hooks reuse `apiFetch`.
- `VerificationRequest.claims` is `requestedClaims` in API/UI; stored as `requested_claims`.
- `ReportExport` is written by Task 8 and referenced by Task 10 UI; route `/reports/{type}/export.csv` is the only export path.
- `DuplicateCase.resolutionCode` values used by Task 10 match Task 5 enum list.

### Review focus tests

Each Review Focus bullet maps to a test in Tasks 5, 8, 11, or 13; no bullet is left without an owning task.

### Proportion

Plan is intentionally longer than a small feature plan because it covers a multi-subsystem MVP, exact role/state/security invariants, and phase gates. Code bodies are not transcribed; signatures, endpoints, rule codes, test names, and acceptance values are pinned.

---

## Phase push checklist

- [ ] Phase 1 pushed after Task 3
- [ ] Phase 2 pushed after Task 7
- [ ] Phase 3 pushed after Task 10
- [ ] Phase 4 pushed after Task 12
- [ ] Phase 5 pushed after Task 14

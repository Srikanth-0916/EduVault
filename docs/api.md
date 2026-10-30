# APAAR-SDMV API Contract (Prototype)

Base path: `/api/v1`  
Content type: `application/json` unless a CSV upload/download.  
All data is synthetic. External verification adapters are mock/sandbox.

## Authentication

`POST /auth/login`

```json
{ "email": "operator@demo-ait.edu", "password": "Demo@1234" }
```

Response:

```json
{
  "accessToken": "<jwt>",
  "expiresIn": 1800,
  "user": {
    "id": "usr_...",
    "email": "operator@demo-ait.edu",
    "fullName": "Arjun Nair",
    "roles": ["INSTITUTION_OPERATOR"],
    "primaryRole": "INSTITUTION_OPERATOR",
    "institutionId": "inst_ait",
    "institutionName": "Aarav Institute of Technology (Demo)",
    "studentIdentityId": null,
    "mfaEnabled": false
  }
}
```

Send the token as `Authorization: Bearer <jwt>`.

`GET /auth/me` returns the same `user` shape. Tokens expire after 30 minutes. Passwords are Argon2 hashes; failed logins are audited without the password.

## Error envelope

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have access to this resource.",
    "details": null
  },
  "traceId": "..."
}
```

Common statuses: `400 VALIDATION_ERROR`, `401 UNAUTHENTICATED`, `403 FORBIDDEN`, `404 NOT_FOUND`, `409 CONFLICT`, `410 VERIFICATION_UNAVAILABLE`, `413 PAYLOAD_TOO_LARGE`, `429 RATE_LIMITED`.

## Roles

`INSTITUTION_ADMIN`, `INSTITUTION_OPERATOR`, `INSTITUTION_NODAL_OFFICER`, `AICTE_REVIEWER`, `AICTE_SUPERVISOR`, `AICTE_ANALYST`, `SYSTEM_ADMIN`, `STUDENT`, `EXTERNAL_VERIFIER`, `AUDITOR`.

Institution roles are always scoped to the authenticated membership's institution. AICTE reviewers/supervisors/auditors/system administrators may traverse institutions only on routes that explicitly allow it. Analysts receive aggregate-only data. Students may access only their own linked record. External verifiers receive only the claims in a consented token.

## Master data and intake

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/institutions/me` | institution roles | Own institution profile |
| GET | `/institutions/me/campuses` | institution roles | Own campuses |
| GET | `/institutions/me/programmes?academicYear=` | institution roles | Own approved programmes |
| GET | `/institutions/me/intake?academicYear=` | institution roles | Read-only approved intake |
| GET | `/institutions/me/users` | institution admin | Own institution users |
| POST | `/institutions/me/users/invitations` | institution admin | Creates demo invitation; returns one-time temp password |
| GET | `/institutions?search=&page=&pageSize=` | AICTE supervisor/system admin/reviewer | Institution directory |
| POST | `/institutions` | AICTE supervisor/system admin | Create institution |
| GET | `/institutions/{id}` | authorized AICTE / own institution | Profile with campuses/programmes |
| POST | `/institutions/{id}/campuses` | AICTE supervisor/system admin | Create campus |
| POST | `/campuses/{id}/programmes` | AICTE supervisor/system admin | Create programme |
| GET | `/programmes?institutionId=&academicYear=` | authorized | Programme list |
| GET | `/intake?programmeId=&academicYear=` | authorized | Snapshot + allocations |
| POST | `/programmes/{id}/intake-snapshots` | AICTE supervisor/system admin | New version; supersedes older |
| PATCH | `/intake-allocations/{id}` | AICTE supervisor/system admin | Correct a draft/current allocation with reason |

Institution users receive `403` on any intake write. Approved intake is versioned by `programme_id + academic_year + version`; the snapshot includes regular and supernumerary allocations separately. Supernumerary allocation should carry an authorization reference.

## Enrolments

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/enrollments?academicYear=&programmeId=&enrollmentStatus=&search=&page=&pageSize=` | institution roles / authorized AICTE read | Tenant-scoped list; masked APAAR |
| POST | `/enrollments` | institution admin/operator | Creates a draft record |
| GET | `/enrollments/{id}` | own institution / authorized AICTE | Detail, versions, findings, verification |
| PATCH | `/enrollments/{id}` | institution admin/operator | Correction; creates a new version |
| POST | `/enrollments/{id}/verify-identity` | institution roles / reviewer | Runs `MockApaarProvider`; response is mock-labelled |
| GET | `/students/me` | student | Own masked identity, enrollments, shares |

Create payload:

```json
{
  "institutionStudentId": "AIT-CSE26-001",
  "campusId": "camp_ait_main",
  "programmeId": "prog_ait_cse",
  "academicYear": "2026-27",
  "admissionDate": "2026-08-10",
  "exitDate": null,
  "apaarId": "123456789012",
  "studentName": "Synthetic Student",
  "dateOfBirth": null,
  "gender": null,
  "enrollmentStatus": "ACTIVE",
  "seatClassification": "APPROVED_REGULAR",
  "admissionCategory": "GENERAL",
  "nriStatus": "NO",
  "ociStatus": "UNKNOWN",
  "foreignNationalStatus": "NO",
  "approvalReference": null
}
```

`apaarId` is optional; omission creates a `MISSING` identity flag. A format-valid value creates `FORMAT_VALID`, not a verified identity. Responses expose only `apaarMasked` (e.g. `••••••••9012`).

## Submission batches

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/submission-batches?academicYear=&status=&page=` | institution roles / AICTE review | Scoped list |
| POST | `/submission-batches` | institution admin/operator/nodal | `{academicYear, campusId?, programmeId?, sourceType:"CSV"}` |
| POST | `/submission-batches/{id}/file` | institution admin/operator/nodal | multipart `file`; CSV ≤5 MB, ≤10,000 rows |
| POST | `/submission-batches/{id}/validate` | institution admin/operator/nodal | Runs rules; returns summary/findings |
| GET | `/submission-batches/{id}` | own institution / authorized AICTE | Batch, rows, findings, timeline |
| GET | `/submission-batches/{id}/results` | own institution / authorized AICTE | Row-level results |
| PATCH | `/submission-batches/{id}/rows/{rowId}` | institution admin/operator/nodal | Edit row while draft/returned |
| POST | `/submission-batches/{id}/attest` | institution nodal officer only | `{declaration:true, attestationName}` |
| POST | `/submission-batches/{id}/submit` | institution nodal officer only | Requires attestation and zero blocking errors |
| POST | `/submission-batches/{id}/decision` | AICTE reviewer/supervisor | `{decision:"ACCEPT"|"RETURN"|"REJECT", reasonCode, reason}` |
| GET | `/submission-batches/template.csv` | institution roles | Download CSV template |
| GET | `/submission-batches/{id}/receipt` | own institution / AICTE | Submission receipt (HMAC-signed payload) |

Batch statuses: `DRAFT`, `VALIDATING`, `VALIDATION_FAILED`, `READY_FOR_ATTESTATION`, `SUBMITTED`, `UNDER_AICTE_REVIEW`, `RETURNED_FOR_CORRECTION`, `ACCEPTED`, `REJECTED`.

CSV columns:

```text
institution_student_id,apaar_id,student_name,programme_code,campus_code,academic_year,
admission_date,exit_date,enrollment_status,seat_classification,admission_category,
nri_status,oci_status,foreign_national_status,approval_reference,date_of_birth,gender
```

`date_of_birth` and `gender` are optional. Blank tri-state attributes are stored as `UNKNOWN`, never as false.

Validation findings include `ruleId` (`BR-001`…`BR-015`), `code` (e.g. `APAAR_INVALID_FORMAT`), `severity`, `message`, `field`, `rowNumber`, `blocking`, and masked `evidence`.

## Duplicate cases

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/duplicate-cases?status=&severity=&institutionId=` | own institution / AICTE | Scoped list |
| GET | `/duplicate-cases/{id}` | authorized | Masked evidence and history |
| POST | `/duplicate-cases/{id}/resolve` | AICTE reviewer/supervisor | `{resolutionCode, notes}` |
| POST | `/duplicate-cases/{id}/request-information` | AICTE reviewer/supervisor | `{message}` |

Resolution codes: `VALID_TRANSFER`, `PERMITTED_CONCURRENT_ENROLMENT`, `DATA_ERROR`, `UNRESOLVED`, `POLICY_BREACH`. `POLICY_BREACH` requires supervisor confirmation in the UI. Duplicate matches never auto-cancel records.

## Dashboards and reports

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/dashboard/institution?academicYear=` | institution roles | KPIs, programme capacity, identifier/status breakdowns |
| GET | `/dashboard/national?academicYear=&institutionType=&state=` | AICTE reviewer/supervisor/analyst/auditor/system admin | National KPIs and trends |
| GET | `/reports/enrolment?academicYear=&institutionId=&programmeId=&groupBy=` | authorized | Aggregate report |
| GET | `/reports/intake-reconciliation?...` | authorized | Approved vs reported, evidence |
| GET | `/reports/data-quality?...` | authorized | Completeness/identifier/rule metrics |
| GET | `/reports/{type}/export.csv?...` | role-scoped | Audited CSV download; formula-injection neutralized |

`AICTE_ANALYST` exports are aggregate-only and suppress groups smaller than 5. Institution exports are scoped to the institution and may include masked student-level rows only for authorized institution roles. Every export writes a `ReportExport` and audit event.

## Consent and public verification

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/verification-requests` | student | Create purpose-bound request |
| GET | `/verification-requests?scope=mine|all&status=` | student/AICTE | Scoped list |
| GET | `/verification-requests/{id}` | owner/AICTE | State and claims scope |
| POST | `/verification-requests/{id}/authorize` | student owner | Creates consent + token; token shown once |
| POST | `/verification-requests/{id}/issue-link` | student owner | Fresh link if not revoked |
| POST | `/verification-requests/{id}/revoke` | student owner/supervisor | Revokes future access |
| GET | `/public/verify/{token}` | none (rate-limited) | Minimal disclosure or generic 410 |

Create request:

```json
{
  "recipientName": "Acme HR",
  "recipientOrg": "Acme Demo Pvt Ltd",
  "recipientEmail": "hr@acme-demo.example",
  "purpose": "Employment screening",
  "requestedClaims": ["INSTITUTION", "PROGRAMME", "ENROLMENT_STATUS"],
  "legalBasis": "CONSENT",
  "expiresInHours": 24
}
```

Authorize response:

```json
{
  "requestId": "...",
  "token": "<opaque>",
  "verifyUrl": "http://localhost:3000/verify/<opaque>",
  "expiresAt": "2026-10-31T10:00:00Z",
  "receipt": { "signature": "<hmac>", "keyId": "primary", "algorithm": "HMAC-SHA256" }
}
```

Public disclosure:

```json
{
  "valid": true,
  "demoNotice": "Synthetic demo data. APAAR checks are mock/sandbox.",
  "recipient": { "name": "Acme HR", "org": "Acme Demo Pvt Ltd", "purpose": "Employment screening" },
  "expiresAt": "...",
  "claims": [
    { "key": "INSTITUTION", "label": "Institution", "value": "Aarav Institute of Technology (Demo)", "source": "AICTE_MASTER_DATA", "status": "CURRENT", "asOf": "..." },
    { "key": "PROGRAMME", "label": "Programme", "value": "B.Tech Computer Science", "source": "AICTE_MASTER_DATA", "status": "CURRENT", "asOf": "..." },
    { "key": "ENROLMENT_STATUS", "label": "Enrolment status", "value": "ACTIVE", "source": "INSTITUTION_SUBMITTED", "status": "ACCEPTED_BY_AICTE", "asOf": "..." }
  ],
  "receipt": { "payload": {}, "signature": "<hmac>", "keyId": "primary", "algorithm": "HMAC-SHA256" }
}
```

Allowed claims: `INSTITUTION`, `PROGRAMME`, `ACADEMIC_YEAR`, `ENROLMENT_STATUS`, `RECORD_ACCEPTANCE`, `APAAR_FORMAT_STATUS`, `APAAR_EXTERNAL_STATUS`. Direct identifiers (name, local ID, full APAAR, DOB) are never claims.

Expired, revoked, malformed, or consumed tokens return `410` with a generic body and write a `VerificationAttempt` plus audit event. Every success also writes an attempt and receipt.

## Notifications and audit

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/notifications?unreadOnly=` | authenticated | Recipient-scoped |
| POST | `/notifications/{id}/read` | recipient | Marks read |
| POST | `/notifications/read-all` | authenticated | Marks all own unread |
| GET | `/audit-events?action=&actorId=&resourceType=&resourceRef=&from=&to=&page=` | auditor/supervisor/system admin | Append-only; masked metadata |
| GET | `/admin/users` | system admin | User administration directory |
| PATCH | `/admin/users/{id}/status` | system admin | Audited |
| POST | `/admin/users/{id}/roles` | system admin | Audited; technical admin cannot approve regulatory records |

## Health

`GET /health` → `{ "status": "ok", "version": "0.1.0" }`

## Mock adapters

`MockApaarProvider` is used everywhere in the prototype. Results carry `mock: true`, provider `MOCK_APAAR`, and adapter version `mock-1.0`. Deterministic outcomes: identifiers ending `99` return `MISMATCH`, ending `88` return `UNAVAILABLE`, otherwise `SUCCESS`. A `SUCCESS` from this adapter is never a live APAAR confirmation and must never be displayed as one.

## Pagination

Collection endpoints accept `page` (1-based) and `pageSize` (1–100). Responses use:

```json
{ "items": [], "page": 1, "pageSize": 20, "total": 0 }
```

All timestamps are ISO-8601 UTC. IDs are opaque strings; clients must not parse them.

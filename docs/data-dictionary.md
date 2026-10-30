# Data Dictionary (Prototype)

All values are synthetic. This dictionary documents the prototype schema and the intended purpose/sensitivity of each field. Production retention, lawful basis, and access rules require AICTE/legal approval and are not established here.

Sensitivity: **Public** (non-personal), **Internal** (administrative), **Personal** (student personal data), **Sensitive identifier** (APAAR-derived material), **Security** (secrets/audit).

## Master data

### Institution (`institutions`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID string | Internal | Stable internal key |
| `aicte_institution_code` | string(32), unique | Public | Authoritative institution code |
| `name` | string(255) | Public | Legal/display name |
| `institution_type` | enum | Public | Government/aided/private/deemed/other |
| `status` | enum | Public | Pending/active/suspended/archived |
| `state`, `city` | string | Public | Region reporting |
| `website_url`, `contact_email` | string | Internal | Administrative contact |
| `created_at`, `updated_at` | datetime | Internal | Record lifecycle |

### Campus (`campuses`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `institution_id` | FK | Internal | Tenant scope |
| `campus_code` | string(32) | Public | Unique within institution |
| `name`, `location` | string | Public | Campus identification |
| `status` | enum | Public | Active/inactive/draft |

### Programme (`programmes`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `institution_id`, `campus_id` | FK | Internal | Approval scope |
| `programme_code` | string(32) | Public | Unique within campus |
| `programme_name` | string(255) | Public | Display/report |
| `award_level` | enum | Public | Certificate/diploma/UG/PG/doctoral |
| `duration_years` | int | Public | Programme metadata |
| `status` | enum | Public | Active/inactive/draft |

### ApprovalSnapshot (`approval_snapshots`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `programme_id` | FK | Internal | Scope |
| `academic_year` | string(16) | Public | e.g. `2026-27` |
| `approval_reference` | string(128) | Internal | Authoritative approval evidence |
| `valid_from`, `valid_to` | date | Public | Effective period |
| `issued_by`, `notes` | string | Internal | Provenance |
| `version` | int | Public | Version chain; old versions retained |
| `status` | enum | Public | Active/superseded |

### IntakeAllocation (`intake_allocations`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `approval_snapshot_id` | FK | Internal | Snapshot scope |
| `seat_classification` | enum | Public | `APPROVED_REGULAR`, `APPROVED_SUPERNUMERARY`, `OTHER` |
| `approved_count` | int | Public | Approved seats |
| `authorization_reference` | string(128) | Internal | Required for supernumerary where policy requires |

## Identity and access

### User (`users`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `email` | string(255), unique | Personal | Login identifier |
| `full_name` | string(255) | Personal | Account display |
| `hashed_password` | string(512) | Security | Argon2 hash; never returned |
| `status` | enum | Internal | Pending invitation/active/suspended |
| `mfa_enabled`, `mfa_secret` | bool/string | Security | MFA-ready fields; secret never returned |
| `phone` | string(32) | Personal | Optional administrative contact |
| `student_identity_id` | FK, nullable | Sensitive | Links a STUDENT user to one identity |
| `last_login_at` | datetime | Security | Authentication audit context |

### OrganizationMembership (`organization_memberships`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `user_id` | FK | Internal | Subject |
| `institution_id` | FK, nullable | Internal | Null for national AICTE roles |
| `role` | enum | Internal | RBAC role |
| `scope` | enum | Internal | Institution or national |
| `valid_from`, `valid_to`, `is_active` | date/bool | Internal | Time-bound access |
| `assigned_by` | UUID | Security | Grant provenance |

### StudentIdentity (`student_identities`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Pseudonymous identity key |
| `apaar_ciphertext` | string(512), nullable | Sensitive identifier | Fernet-encrypted APAAR; null for missing/malformed |
| `apaar_lookup_token` | string(64), unique, nullable | Sensitive identifier | Keyed HMAC for exact matching; never displayed |
| `apaar_last4` | string(4), nullable | Sensitive identifier | Only displayable fragment |
| `identifier_status` | enum | Internal | `MISSING` … `CORRECTED` |
| `key_id` | string(64) | Security | Encryption key reference for rotation |
| `verification_reference` | string(128) | Internal | Latest external adapter reference (mock) |

## Enrolment

### StudentEnrollment (`student_enrollments`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `student_identity_id` | FK | Sensitive | Protected identity link |
| `institution_id`, `campus_id`, `programme_id` | FK | Internal | Enrolment scope |
| `student_local_id` | string(128) | Personal | Institution-local enrolment number |
| `student_full_name` | string(255) | Personal | Reconciliation/verification only |
| `academic_year` | string(16) | Internal | Cohort/intake period |
| `admission_date`, `exit_date` | date | Personal | Lifecycle/overlap logic |
| `enrollment_status` | enum | Personal | Pending/active/withdrawn/transferred/completed/cancelled/under review |
| `seat_classification` | enum | Internal | Regular/supernumerary/other |
| `admission_category` | string(64) | Personal | Policy category |
| `nri_status`, `oci_status`, `foreign_national_status` | enum | Personal | `YES`/`NO`/`UNKNOWN`; distinct concepts |
| `supernumerary_approval_reference` | string(128) | Internal | Evidence for special capacity |
| `version`, `is_current`, `supersedes_id` | int/bool/FK | Internal | Version chain |
| `correction_reason` | string(512) | Internal | Why a new version exists |
| `source_batch_id`, `source_row_id` | FK | Internal | Provenance |
| `created_by`, `updated_by` | UUID | Security | Actor provenance |
| `record_accepted_at` | datetime | Internal | AICTE acceptance evidence |

### EnrollmentVersion (`enrollment_versions`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `student_enrollment_id` | FK | Internal | Versioned record |
| `version` | int | Internal | Snapshot number |
| `snapshot` | JSON | Personal | Immutable snapshot; access-controlled |
| `change_reason`, `changed_by`, `actor_role` | string | Internal/Security | Change provenance |
| `created_at` | datetime | Internal | Snapshot time |

## Submission

### SubmissionBatch (`submission_batches`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `institution_id` | FK | Internal | Tenant |
| `academic_year` | string(16) | Internal | Reporting period |
| `source_type` | enum | Internal | Portal/CSV/API/sync |
| `status` | enum | Internal | Canonical batch workflow |
| `version`, `supersedes_batch_id` | int/FK | Internal | Resubmission chain |
| `file_name`, `file_storage_key` | string | Internal | Private source file reference |
| `file_checksum` | string(64) | Internal | SHA-256 integrity evidence |
| `file_size_bytes`, `row_count` | int | Internal | Upload evidence |
| `attested_at`, `attested_by`, `attestation_name`, `declaration_accepted` | datetime/FK/string/bool | Internal/Security | Nodal attestation |
| `submitted_at`, `submitted_by` | datetime/UUID | Internal | Submission evidence |
| `decision`, `decision_reason`, `decision_reason_code`, `decided_at`, `decided_by` | string/datetime | Internal | AICTE decision |
| `assigned_reviewer_id` | UUID | Internal | Review assignment |
| `created_by` | UUID | Security | Uploader |

### SubmissionRow (`submission_rows`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `batch_id` | FK | Internal | Parent batch |
| `source_row_number` | int | Internal | CSV row reference |
| `student_name` | string(255) | Personal | Parsed preview |
| `student_local_id` | string(128) | Personal | Parsed preview |
| `apaar_last4` | string(4) | Sensitive identifier | Masked preview only |
| `student_identity_id` | FK | Sensitive | Resolved identity |
| `enrollment_id` | FK | Internal | Committed enrollment, if any |
| `row_status` | enum | Internal | Pending/valid/warning/error |
| `raw_data` | JSON | Personal | Original row; private; no raw APAAR should be added after parse |
| `parsed_data` | JSON | Personal | Normalized row/evidence |

**Note:** raw CSV bytes are stored privately. Validation findings and audit metadata must contain masked values only. A production design should encrypt the source file and parsed personal data at rest.

### ValidationRun (`validation_runs`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `batch_id` | FK | Internal | Scope |
| `rule_set_version` | string(32) | Public | e.g. `2026.1` |
| `status` | enum | Internal | Running/completed/failed |
| `started_at`, `completed_at`, `duration_ms` | datetime/int | Internal | Performance/evidence |
| `requested_by` | UUID | Security | Actor |
| `summary` | JSON | Internal | Counts by severity/status |

### ValidationFinding (`validation_findings`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `validation_run_id`, `batch_id` | FK | Internal | Scope |
| `row_id`, `record_id` | FK/string | Internal | Subject |
| `rule_id` | string(16) | Public | `BR-001` … `BR-015` |
| `code` | string(64) | Public | Machine-readable code |
| `severity` | enum | Public | INFO/WARNING/HIGH/ERROR |
| `blocking` | bool | Public | Prevents clean submission |
| `message` | string(1024) | Internal | Human correction guidance |
| `field` | string(64) | Internal | Affected field |
| `status` | enum | Internal | Open/resolved/accepted/dismissed |
| `evidence` | JSON | Internal | Masked evidence (never raw APAAR) |

## Review

### DuplicateCase (`duplicate_cases`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id`, `match_group_id` | UUID/string | Internal | Stable key and idempotent match group |
| `match_type` | enum | Internal | Same institution/cross institution/transfer context |
| `severity` | enum | Internal | Review priority |
| `status` | enum | Internal | Open/under review/resolved/dismissed |
| `primary_enrollment_id`, `related_enrollment_id` | FK | Internal | Match sides |
| `institution_id`, `discovered_batch_id` | FK | Internal | Scope/provenance |
| `opened_at`, `assigned_reviewer_id` | datetime/UUID | Internal | Case management |
| `resolution_code`, `resolution_reason`, `resolved_by`, `resolved_at` | enum/string/UUID/datetime | Internal | Decision evidence |
| `evidence` | JSON | Personal (masked) | Dates, institution names, masked IDs, overlap days |

### IdentityVerification (`identity_verifications`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `student_identity_id` | FK | Sensitive | Subject |
| `provider` | string(64) | Public | `MOCK_APAAR` in prototype |
| `provider_reference` | string(128) | Internal | Adapter reference |
| `result` | enum | Internal | SUCCESS/NOT_FOUND/MISMATCH/UNAVAILABLE/… |
| `adapter_version` | string(32) | Public | e.g. `mock-1.0` |
| `is_mock` | bool | Public | Must be true in prototype |
| `checked_at`, `purpose`, `consent_context` | datetime/string | Internal | Purpose-bound evidence |
| `requested_by` | UUID | Security | Actor |
| `detail` | JSON | Internal | Adapter metadata, no raw identifier |
| `resulting_status` | enum | Internal | Identity status after check |

## Verification and consent

### ConsentGrant (`consent_grants`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `subject_user_id`, `student_identity_id` | FK | Sensitive | Data principal |
| `verification_request_id` | FK | Internal | Linked request |
| `recipient_name`, `recipient_org`, `recipient_email` | string | Personal | Specific recipient |
| `purpose` | string(512) | Internal | Stated purpose |
| `fields_scope` | JSON | Internal | Claim allow-list |
| `legal_basis` | enum | Internal | Consent/other approved basis |
| `notice_version` | string(32) | Internal | Notice shown at grant time |
| `single_use` | bool | Internal | Consumption policy |
| `status`, `granted_at`, `expires_at`, `revoked_at`, `consumed_at` | enum/datetime | Internal | Lifecycle |

### VerificationRequest (`verification_requests`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `subject_user_id`, `student_identity_id` | FK | Sensitive | Subject |
| `created_by` | UUID | Security | Initiator |
| `recipient_name`, `recipient_org`, `recipient_email` | string | Personal | Verifier identity |
| `purpose` | string(512) | Internal | Purpose limitation |
| `requested_claims` | JSON | Internal | Allow-listed claims |
| `legal_basis` | enum | Internal | Basis |
| `expires_in_hours` | int | Internal | Requested link lifetime (1–168 h) |
| `status` | enum | Internal | Pending/authorized/viewed/consumed/expired/revoked/denied |
| `single_use` | bool | Internal | Replay policy |
| `token_hash`, `token_jti` | string | Security | Token material; raw token never stored |
| `issued_at`, `expires_at`, `viewed_at`, `consumed_at`, `revoked_at`, `revoked_reason` | datetime/string | Internal | Lifecycle |

### VerificationReceipt (`verification_receipts`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `verification_request_id` | FK | Internal | Scope |
| `claims_hash` | string(64) | Internal | Integrity of disclosed claims |
| `payload` | JSON | Personal (disclosed claims only) | Signed receipt content |
| `signature` | string(512) | Security | HMAC-SHA256 |
| `key_id` | string(64) | Security | Signing key reference |
| `issued_at`, `expires_at`, `created_at` | datetime | Internal | Validity |

### VerificationAttempt (`verification_attempts`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `verification_request_id` | FK, nullable | Internal | Resolved request, if any |
| `outcome` | enum | Security | Success/denied |
| `denial_reason` | enum | Security | Expired/revoked/invalid/consumed |
| `claims_disclosed` | JSON | Personal | Minimal field list disclosed |
| `ip_address`, `user_agent`, `trace_id` | string | Security | Request evidence |
| `attempted_at` | datetime | Security | Time |
| `receipt_id` | FK | Internal | Issued receipt |

## Operations

### AuditEvent (`audit_events`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `actor_id`, `actor_email`, `actor_role` | string | Security | Actor |
| `action` | string(96) | Security | e.g. `BATCH_SUBMITTED` |
| `outcome` | enum | Security | Success/denied/failure |
| `resource_type`, `resource_ref` | string | Security | Subject |
| `institution_id` | FK | Security | Tenant scope |
| `reason` | string(1024) | Security | Human reason where required |
| `metadata_` | JSON | Security | Masked context only |
| `ip_address`, `user_agent`, `trace_id` | string | Security | Request context |
| `timestamp` | datetime | Security | Append-only event time |

### Notification (`notifications`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `recipient_user_id`, `institution_id` | FK | Internal | Recipient/scope |
| `event_type` | string(96) | Internal | Event category |
| `title`, `body` | string | Internal | Safe copy; no student identifiers |
| `channel` | enum | Internal | In-app/mock email |
| `delivery_status` | enum | Internal | Queued/sent/mocked/failed |
| `resource_type`, `resource_ref` | string | Internal | Deep link target |
| `read_at` | datetime | Personal | Read state |

### ReportExport (`report_exports`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `report_type` | string(64) | Internal | Enrolment/intake/data quality |
| `requested_by`, `requested_role` | string | Security | Actor |
| `institution_id` | FK | Internal | Scope |
| `filters` | JSON | Internal | Reproducibility |
| `row_count`, `format` | int/string | Internal | Export metadata |
| `file_storage_key` | string(512) | Internal | Private generated file |
| `generated_at` | datetime | Internal | Freshness |
| `contains_direct_identifiers` | bool | Security | Leakage guard |

### IntegrationClient (`integration_clients`)

| Field | Type | Sensitivity | Purpose |
|---|---|---|---|
| `id` | UUID | Internal | Stable key |
| `organization_name` | string(255) | Internal | Client organization |
| `contact_email` | string(255) | Personal | Administrative contact |
| `scopes` | JSON | Security | Allowed API scopes |
| `credential_ref` | string(255) | Security | Reference to secret manager entry; no raw secret |
| `status` | enum | Internal | Active/suspended/revoked |
| `read_only` | bool | Internal | Mutation guard |
| `last_used_at` | datetime | Security | Monitoring |

## Data minimization and retention

- Do not collect Aadhaar number, passport number, parent names, personal mobile numbers, or unrelated identity data.
- Name and date of birth are optional where not required for reconciliation/verification; the prototype collects them only for demonstration.
- Raw APAAR values must never be logged, exported, put in URLs, or shown in list views.
- Retention periods are **not** set by this prototype. Production must define retention for source CSV files, enrollment records, verification evidence, consent records, and audit logs with AICTE/legal approval.

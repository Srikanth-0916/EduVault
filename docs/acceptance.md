# MVP Acceptance Mapping

This maps PRD §22 acceptance criteria to prototype evidence. Automated tests are added as phases complete; manual checks are marked.

## Identity and access

| Criterion | Evidence |
|---|---|
| Institution and AICTE users sign in with separate role scopes | Auth tests + login demo accounts |
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
| Institution can upload CSV and inspect row-level results | Batch upload/validation tests + wizard |
| Original file, uploader, checksum, time retained | Batch model fields + receipt |
| Invalid rows are not silently committed | Blocking-error submission test |
| Nodal attestation required before submission | 409 without attestation test + nodal-only guard |

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
| AICTE can accept/return/reject with reason | Decision tests + review UI |
| Institution can correct and resubmit returned batch | Return/resubmit test + editor |
| Dashboards show intake, enrolment, validation, cases | Dashboard endpoints + pages |
| Reports filter by year/institution/programme | Report API tests + UI filters |

## Verification and security

| Criterion | Evidence |
|---|---|
| External verification shows only authorized claims | Public verify test + claim cards |
| Expired/revoked references cannot disclose | 410 tests + denied state |
| Attempts/disclosures audited | Attempt/audit tests |
| APAAR masked in routine views, excluded from logs | Encryption/masking/log-redaction tests |
| Demo uses synthetic data only | Seed + banner + docs |

## Manual demo acceptance

- [ ] All key flows run without manual database edits.
- [ ] Mock integrations visibly labelled.
- [ ] One malformed APAAR, one duplicate, one intake exception, one verification request handled correctly.
- [ ] No institution sees another institution's private student data.
- [ ] Reviewer can explain every flag and next action.

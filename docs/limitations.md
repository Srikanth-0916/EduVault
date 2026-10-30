# Limitations and Non-Claims

This repository is a **hackathon/demo prototype**. It is not an AICTE production system, not a certification, and not authorized to process real student data.

## What this prototype is not

- It does **not** create, issue, modify, or deactivate APAAR IDs.
- It does **not** replace APAAR, the Academic Bank of Credits (ABC), DigiLocker, NAD, or an institution's SIS.
- It does **not** call live APAAR/ABC/DigiLocker/NAD/Aadhaar/AICTE APIs. All external verification is a clearly labelled mock/sandbox adapter.
- It does **not** verify a degree, marksheet, certificate, or transcript. A verified enrolment claim is not a degree verification.
- It does **not** make automatic admission, eligibility, scholarship, accreditation, or penalty decisions.
- It does **not** label a duplicate match as fraud. Cases require human review.
- It does **not** provide a public student search or bulk lookup.
- It does **not** implement production MFA/OIDC, managed KMS, database encryption at rest, WAF, SIEM, backup/DR, or penetration testing.
- It does **not** implement a formal privacy notice, data-subject request workflow, retention schedule, or guardian/minor flow.
- It does **not** implement a production migration path; the prototype creates tables directly. A production build should use a migration tool.
- It does **not** use a message queue; validation and notifications run synchronously. The 10,000-row benchmark is a target, not a production SLA.

## Environment and data limitations

- All seeded institutions, students, identifiers, and outcomes are synthetic. Demo institution names are fictional and marked “(Demo)”.
- APAAR-shaped values are test values and are not real identifiers.
- Mock adapter outcomes are deterministic and not evidence of identity.
- The demo accounts use a shared password and are not suitable for any real deployment.
- The browser stores the demo JWT in local storage; production should use OIDC with secure, httpOnly session handling.
- The in-process rate limiter is per worker and resets on restart.
- SQLite is used in tests; runtime uses PostgreSQL. Some database-specific behavior (row locking, partial indexes) may differ.
- English only in this release.
- CSV is the only export format; XLSX/PDF are not implemented. Small-group suppression is applied for analyst aggregate exports, but policy thresholds require approval.
- QR codes are generated client-side from the opaque verification URL; certificate issuance and printing workflows are out of scope.

## Policy items that remain open

The PRD's open questions (authoritative identifiers, submission frequency, APAAR mandatoriness, seat/category rules, transfer/concurrent enrolment rules, decision authority, legal basis, retention, certificate wording, identity federation, hosting standards, scale targets) are **not resolved** by this prototype. Configurable sample rules are used and must not be treated as AICTE policy.

## Safety and reporting

- Do not load real personal data into this application.
- Do not present mock outcomes as official verification.
- If this repository is used as a base for a real system, complete the production hardening checklist in `docs/security.md`, obtain written authorization for any external integration, and complete legal/privacy review.

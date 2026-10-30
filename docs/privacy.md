# Privacy and DPDP Notes (Prototype)

This is an engineering/POC note, not legal advice. The PRD requires AICTE and participating institutions to confirm the legal basis, data-fiduciary/processor roles, retention, and consent mechanics before any production use. India's Digital Personal Data Protection Act, 2023 and the Digital Personal Data Protection Rules, 2025 (phased commencement) must be assessed by the project's legal owner at deployment time.

## Processing purposes represented in the prototype

1. **Regulatory enrolment reporting** — institution-submitted student-level enrolment linked to APAAR, reconciled against approved intake, for AICTE oversight.
2. **Data-quality and duplicate review** — detect missing/malformed/duplicate identifiers and capacity exceptions; route consequential cases to humans.
3. **Controlled third-party verification** — only where a student authorizes a specific recipient, purpose, claim set, and duration (or another approved lawful basis applies).
4. **Audit and accountability** — record material actions, decisions, exports, and verification attempts.

The prototype does **not** process Aadhaar numbers, issue APAAR IDs, issue degrees, or replace APAAR/ABC/DigiLocker/NAD.

## Data minimization

- APAAR is collected only as an academic identifier. It is never an authentication secret.
- Name/date of birth are included in the demo only to support reconciliation and verification illustrations; production must confirm necessity.
- NRI, OCI, and foreign-national status are distinct tri-state attributes (`YES`/`NO`/`UNKNOWN`) and not seat classifications.
- No parent names, mobile numbers, Aadhaar, passport, biometrics, or unrelated high-risk identifiers.
- Aggregate analytics are the default for AICTE analysts; direct identifiers are excluded.

## Consent and lawful basis

The prototype distinguishes:

- **Mandatory regulatory processing** — AICTE/institution processing for approved regulatory purposes. The legal basis must be documented by the authorities; consent is not assumed to be the sole basis.
- **Optional third-party disclosure** — a student-mediated authorization with recipient, purpose, fields, notice version, time, expiry, and revocation. Consent is specific and not bundled with unrelated terms.

A consent grant records recipient name/org/email, purpose, claim scope, legal basis, notice version, grant time, expiry, status, and revocation. A verification request cannot authorize itself; the student owner must perform the authorization. Revocation stops future public resolution of the token.

Guardian/minor flows are **not implemented**. Production must configure an approved representative flow after legal/policy review.

## Data subject rights (prototype posture)

| Right | Prototype support | Production gap |
|---|---|---|
| Information/notice | Demo notice shown on student portal; consent review step | Formal notice, translations, accessibility review |
| Access | Student `GET /students/me` returns own masked record | Full data-access request workflow |
| Correction | Institution correction workflow creates a new version; student can see the route | Formal request tracking/SLA |
| Withdrawal of consent | Revoke action stops future token access | Legal review of effect on prior disclosures |
| Grievance | Documented support route placeholder | Designated grievance officer and process |
| Erasure | Not implemented; regulatory retention may override | Retention schedule and legal assessment |
| Portability | Institution export of own records (CSV) | Approved format/scope |

## Disclosure minimization

- Public verification returns only granted claims, never name/local ID/full APAAR/DOB.
- Each claim carries its source and status; a successful token resolution is not a degree verification.
- Denials are generic and do not confirm whether a record or token existed.
- Attempts (success and denial) are recorded with IP/user agent/trace ID, but not the raw token.
- Receipts contain only the disclosed claims and a signature; they are not degree certificates.

## Retention (placeholder)

The prototype does not enforce retention. Before production, define and implement retention for:

- source CSV files and parsed rows,
- current and historical enrolment versions,
- validation findings,
- duplicate cases and decisions,
- consent grants and verification attempts/receipts,
- audit events,
- report exports and generated files,
- account and membership records.

Audit and regulatory evidence may need longer retention than operational data; the legal owner must decide. Backups must follow the same retention and deletion rules.

## Security linkage

APAAR values are Fernet-encrypted with a keyed HMAC lookup token; only last-4 is displayed. Raw values must not appear in logs, analytics, URLs, or exports. Production requires managed keys, rotation, field-level access control, and database encryption. See `docs/security.md`.

## Demo-only statement

Every record in this repository is synthetic. Mock adapters are labelled. Do not load real student data into this prototype. The repository is not approved for production processing.

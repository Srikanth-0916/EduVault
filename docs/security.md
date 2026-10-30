# Security Model and Threat Notes (Prototype)

This document describes the prototype's security posture and the gaps that must be closed before handling real student data. It is not a certification or a substitute for AICTE security review, threat modelling, penetration testing, or legal advice.

## Assets

1. Student identity and enrolment records (personal data).
2. APAAR identifiers and derived tokens (sensitive identifiers).
3. Approved intake and AICTE review decisions (regulatory data).
4. Consent grants, verification tokens, and disclosure receipts.
5. Audit trail and export history.
6. Credentials, signing keys, and encryption keys.

## Trust boundaries

- Browser ↔ Next.js web server.
- Browser/Next.js ↔ FastAPI API.
- API ↔ PostgreSQL.
- API ↔ private file storage (`var/storage` in the prototype; S3/MinIO in production).
- API ↔ external verification adapters (mock only in this build).
- Student/verifier ↔ public verification endpoint (unauthenticated, rate-limited).

## Controls implemented

| Area | Control |
|---|---|
| Authentication | Email + Argon2 password hash; 30-minute HS256 JWT; generic login errors; login attempts audited |
| Authorization | Role memberships, institution scope on every object lookup, server-side role guards, AICTE/analyst separation |
| Tenant isolation | Institution ID resolved from the authenticated membership, never from request payload; cross-tenant attempts audited |
| APAAR at rest | Fernet ciphertext + keyed HMAC-SHA256 lookup token; last-4 display only; raw value never logged/exported |
| APAAR in use | 12-digit format check only; external state is separate; mock results labelled |
| Uploads | `.csv` extension, content-type, ≤5 MB, ≤10,000 rows, header allow-list, UTF-8 BOM tolerance, SHA-256 checksum, private storage |
| Validation | Rule IDs/codes/severity/evidence; blocking errors gate submission; no silent acceptance |
| Workflow | Canonical state machine; nodal attestation required; reviewer decisions with reason; illegal transitions rejected |
| Consent | Purpose, recipient, claim scope, notice version, expiry, revocation; no bundled/unlimited consent |
| Verification tokens | 32 random bytes, URL-safe, hashed at rest, server-side expiry/revocation, optional single-use |
| Public disclosure | Minimal claims, claim-by-claim source/status, generic 410 denial, attempts logged |
| Receipts | HMAC-SHA256 canonical JSON, key ID/algorithm exposed, payload integrity hash |
| Audit | Append-only application table, no update/delete routes, masked metadata, actor/IP/UA/trace |
| Exports | Role/field scoping, aggregate-only analyst path, small-group suppression, formula-injection neutralization, audited |
| Transport | TLS terminated by deployment; CORS restricted to configured origins; security headers |
| Rate limits | Login `10/min/IP`, public verification `30/min/IP`; `429` + `Retry-After` with trace/security headers; prototype in-process sliding window |
| Secrets | Environment variables; production startup refuses development defaults |
| Errors | Structured envelope with trace ID; no stack traces or raw values |
| Logging | No request bodies for auth/verification/upload; redaction filter for 12-digit sequences, bearer tokens and sensitive key/value pairs |
| Headers | `nosniff`, frame denial, referrer policy, permissions policy, CSP, CORP/COOP, `noindex`, `no-store`; `Server` banner removed; HSTS in production |
| Startup | Development/test-only auto-seed; production never seeds; test env does not create schema implicitly |

## Threat model (STRIDE summary)

| Threat | Example | Mitigation | Residual risk |
|---|---|---|---|
| Spoofing | Stolen JWT | Short expiry, HTTPS, production OIDC/MFA | Prototype stores JWT in browser storage; XSS would expose it |
| Tampering | Institution edits approved intake | Server-side AICTE role check, immutable snapshots, audit | Prototype admin can change seed data directly in DB |
| Repudiation | Reviewer denies decision | Append-only audit with actor/reason/time | App DB admin could alter rows; production needs WORM/ledger |
| Information disclosure | Cross-tenant student read | Scope checks, tests, masked APAAR, analyst aggregates | No field-level DB encryption; production DB encryption required |
| Denial of service | Upload flood, token brute force | Size/row limits, rate limits, timeouts | In-process limiter is per-worker; production needs Redis/WAF |
| Elevation of privilege | Operator attests batch | Nodal-only guard, system admin cannot decide | Membership administration is prototype-only |
| Injection | CSV formula injection | Prefix `'` for `= + - @` on export | Other spreadsheet risks possible |
| SSRF | Adapter URL injection | Mock adapter only; production allow-list/egress policy | Not implemented for live providers |
| Supply chain | Malicious dependency | Lockfiles, CI; scans not yet automated | Production needs SCA/image scanning |
| Prompt injection via target content | Uploaded CSV cells instructing an AI | No LLM processes uploaded content; treat data as data | Not applicable in current build |

## Privacy principles

- Collect only fields needed for the demonstrated regulatory/verification flow.
- Separate mandatory regulatory processing from optional third-party sharing.
- Display APAAR format validity, mock external status, AICTE acceptance, and credential verification as distinct claims.
- Mask identifiers in routine UI, reports, and audit metadata.
- Never include student data in notification subjects or public URLs beyond the opaque token.
- Provide a correction route via institution workflows; consent withdrawal via revocation.
- Use synthetic data only in this repository and demo.

## Production hardening checklist (not implemented)

- OIDC/OAuth 2.0 identity provider with MFA for privileged roles.
- Managed KMS/HSM for APAAR encryption, lookup HMAC, JWT, and receipt keys; documented rotation/re-tokenization.
- Database encryption at rest, TLS in transit, row-level security or equivalent.
- Redis-backed rate limiting and queueing; Celery/RQ workers; dead-letter handling.
- S3/MinIO private buckets with malware scanning, retention, and object-lock for audit evidence.
- WAF, DDoS protection, centralized SIEM, alerting for bulk access/cross-tenant attempts.
- Formal DPIA, privacy notice, data-subject request workflow, retention schedule, breach response.
- Independent penetration test, threat model review, dependency/container scanning, backup/restore test.
- Access recertification, break-glass procedure, segregation of duties.
- API versioning, signed webhooks, integration credential rotation, partner onboarding.
- Real legal review of consent basis, certificate wording, and data-fiduciary roles.

## Security test coverage in this repo

- Authentication success/failure, generic errors, role guards.
- Institution tenant isolation across enrolments, batches, cases, reports.
- APAAR format validation, encryption/HMAC roundtrip, masking, mock outcomes.
- Blocking validation, attestation requirement, illegal workflow transitions.
- Verification token expiry/revocation, generic denial, attempt auditing.
- Upload size/row/header limits, CSV injection neutralization.
- Audit append-only route surface and metadata redaction.
- Rate limiting on login/public verification, including `Retry-After` and
  independent buckets per route/IP.
- Upload extension/media-type/size/row/encoding/header guards.
- Log-filter redaction of APAAR-shaped digits, bearer tokens and sensitive
  fields.
- Secret validation in production mode.
- Playwright browser flows for dashboard, batch→attest→review, consent→public
  verification→revocation, and generic unknown-token denial.
- 10,000-row validation benchmark (`scripts/benchmark_validation.py`).

See `docs/limitations.md` for what this prototype deliberately does not claim.

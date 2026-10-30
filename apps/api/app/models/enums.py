"""Canonical enum values for every workflow/table in the prototype.

All enum columns store the string *value* (native DB enums are avoided for
SQLite/Postgres portability, design §5.2). The uppercase values below are the
canonical API strings.
"""

from __future__ import annotations

from enum import StrEnum


class InstitutionType(StrEnum):
    GOVERNMENT = "GOVERNMENT"
    GOVERNMENT_AIDED = "GOVERNMENT_AIDED"
    PRIVATE_SELF_FINANCED = "PRIVATE_SELF_FINANCED"
    DEEMED_UNIVERSITY = "DEEMED_UNIVERSITY"
    OTHER = "OTHER"


class InstitutionStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class AwardLevel(StrEnum):
    CERTIFICATE = "CERTIFICATE"
    DIPLOMA = "DIPLOMA"
    PG_DIPLOMA = "PG_DIPLOMA"
    UNDERGRADUATE = "UNDERGRADUATE"
    POSTGRADUATE = "POSTGRADUATE"
    DOCTORAL = "DOCTORAL"


class RecordStatus(StrEnum):
    """Generic status for master-data and configuration records."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class SeatClassification(StrEnum):
    APPROVED_REGULAR = "APPROVED_REGULAR"
    APPROVED_SUPERNUMERARY = "APPROVED_SUPERNUMERARY"
    OTHER = "OTHER"


class ApprovalSnapshotStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class UserRole(StrEnum):
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    INSTITUTION_OPERATOR = "INSTITUTION_OPERATOR"
    INSTITUTION_NODAL_OFFICER = "INSTITUTION_NODAL_OFFICER"
    AICTE_REVIEWER = "AICTE_REVIEWER"
    AICTE_SUPERVISOR = "AICTE_SUPERVISOR"
    AICTE_ANALYST = "AICTE_ANALYST"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    AUDITOR = "AUDITOR"
    STUDENT = "STUDENT"
    EXTERNAL_VERIFIER = "EXTERNAL_VERIFIER"


class UserStatus(StrEnum):
    PENDING_INVITATION = "PENDING_INVITATION"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class MembershipScope(StrEnum):
    INSTITUTION = "INSTITUTION"
    NATIONAL = "NATIONAL"


class IdentityStatus(StrEnum):
    MISSING = "MISSING"
    MALFORMED = "MALFORMED"
    FORMAT_VALID = "FORMAT_VALID"
    PENDING_EXTERNAL_CHECK = "PENDING_EXTERNAL_CHECK"
    EXTERNALLY_CONFIRMED = "EXTERNALLY_CONFIRMED"
    EXTERNAL_MISMATCH = "EXTERNAL_MISMATCH"
    EXTERNAL_UNAVAILABLE = "EXTERNAL_UNAVAILABLE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CORRECTED = "CORRECTED"


class EnrollmentStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    TRANSFERRED = "TRANSFERRED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    UNDER_REVIEW = "UNDER_REVIEW"


class CapacityStatus(StrEnum):
    WITHIN_APPROVED_INTAKE = "WITHIN_APPROVED_INTAKE"
    WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY = (
        "WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY"
    )
    POSSIBLE_EXCESS = "POSSIBLE_EXCESS"
    MISSING_APPROVAL_DATA = "MISSING_APPROVAL_DATA"
    PENDING_RULE_REVIEW = "PENDING_RULE_REVIEW"


class BatchStatus(StrEnum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    READY_FOR_ATTESTATION = "READY_FOR_ATTESTATION"
    SUBMITTED = "SUBMITTED"
    UNDER_AICTE_REVIEW = "UNDER_AICTE_REVIEW"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RowStatus(StrEnum):
    PENDING = "PENDING"
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Severity(StrEnum):
    """Shared severity scale for validation findings and duplicate cases."""

    INFO = "INFO"
    LOW = "LOW"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationRunStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class BatchSourceType(StrEnum):
    CSV_UPLOAD = "CSV_UPLOAD"
    MANUAL_ENTRY = "MANUAL_ENTRY"
    API_INTEGRATION = "API_INTEGRATION"


class DuplicateCaseStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    WITHDRAWN = "WITHDRAWN"


class DuplicateMatchType(StrEnum):
    WITHIN_BATCH = "WITHIN_BATCH"
    SAME_INSTITUTION = "SAME_INSTITUTION"
    CROSS_INSTITUTION = "CROSS_INSTITUTION"


class CaseResolutionCode(StrEnum):
    VALID_TRANSFER = "VALID_TRANSFER"
    PERMITTED_CONCURRENT_ENROLMENT = "PERMITTED_CONCURRENT_ENROLMENT"
    DATA_ERROR = "DATA_ERROR"
    UNRESOLVED = "UNRESOLVED"
    POLICY_BREACH = "POLICY_BREACH"


class ApaarProviderOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNSUPPORTED = "UNSUPPORTED"


class VerificationRequestStatus(StrEnum):
    PENDING_AUTHORIZATION = "PENDING_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    VIEWED = "VIEWED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class VerificationClaim(StrEnum):
    INSTITUTION = "INSTITUTION"
    PROGRAMME = "PROGRAMME"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"
    ENROLMENT_STATUS = "ENROLMENT_STATUS"
    RECORD_ACCEPTANCE = "RECORD_ACCEPTANCE"
    APAAR_FORMAT_STATUS = "APAAR_FORMAT_STATUS"
    APAAR_EXTERNAL_STATUS = "APAAR_EXTERNAL_STATUS"


class LegalBasis(StrEnum):
    CONSENT = "CONSENT"
    STATUTORY_AUTHORITY = "STATUTORY_AUTHORITY"
    CONTRACT = "CONTRACT"
    LEGITIMATE_INTEREST = "LEGITIMATE_INTEREST"


class ConsentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class AttemptOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"


class AttemptDenialReason(StrEnum):
    NOT_FOUND = "NOT_FOUND"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    CONSUMED = "CONSUMED"
    MALFORMED = "MALFORMED"


class AuditOutcome(StrEnum):
    """Outcome recorded on audit events for the attempted action."""

    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    VOID = "VOID"


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class NotificationDeliveryStatus(StrEnum):
    QUEUED = "QUEUED"
    DELIVERED = "DELIVERED"
    MOCKED = "MOCKED"
    FAILED = "FAILED"


class ReportType(StrEnum):
    ENROLMENT = "ENROLMENT"
    INTAKE_RECONCILIATION = "INTAKE_RECONCILIATION"
    DATA_QUALITY = "DATA_QUALITY"


class DeclaredStatus(StrEnum):
    """Tri-state declared attribute values (blank/unknown never means false)."""

    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class IntegrationClientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


def sa_enum_values(enum_cls: type) -> list[str]:
    """Values list for SAEnum(native_enum=False, values_callable=...)."""
    return [member.value for member in enum_cls]  # type: ignore[attr-defined]

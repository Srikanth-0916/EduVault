"""SQLAlchemy model layer grouped by domain (design §5.2).

Importing this package imports every model so ``Base.metadata.create_all``
creates all prototype tables.
"""

from __future__ import annotations

from app.models.base import Base, TimestampMixin, pk, sa_enum, utc_now, uuid_fk
from app.models.batch import (
    SubmissionBatch,
    SubmissionRow,
    ValidationFinding,
    ValidationRun,
)
from app.models.enrollment import EnrollmentVersion, StudentEnrollment
from app.models.enums import sa_enum_values
from app.models.identity import StudentIdentity
from app.models.master import (
    ApprovalSnapshot,
    Campus,
    Institution,
    IntakeAllocation,
    OrganizationMembership,
    Programme,
    User,
)
from app.models.ops import (
    AuditEvent,
    IntegrationClient,
    Notification,
    ReportExport,
)
from app.models.review import DuplicateCase, IdentityVerification
from app.models.verification import (
    ConsentGrant,
    VerificationAttempt,
    VerificationReceipt,
    VerificationRequest,
)

__all__ = [
    "ApprovalSnapshot",
    "AuditEvent",
    "Base",
    "Campus",
    "ConsentGrant",
    "DuplicateCase",
    "EnrollmentVersion",
    "IdentityVerification",
    "Institution",
    "IntakeAllocation",
    "IntegrationClient",
    "Notification",
    "OrganizationMembership",
    "Programme",
    "ReportExport",
    "StudentEnrollment",
    "StudentIdentity",
    "SubmissionBatch",
    "SubmissionRow",
    "TimestampMixin",
    "User",
    "ValidationFinding",
    "ValidationRun",
    "VerificationAttempt",
    "VerificationReceipt",
    "VerificationRequest",
    "pk",
    "sa_enum",
    "sa_enum_values",
    "utc_now",
    "uuid_fk",
]

__version__ = "0.1.0"

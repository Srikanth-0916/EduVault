"""Capacity calculations against the active approval snapshot.

Regular and supernumerary allocations are always reported separately. NRI,
OCI and foreign-national flags are attributes and never change the seat
classification for capacity purposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.enrollment import StudentEnrollment
from app.models.enums import (
    ApprovalSnapshotStatus,
    CapacityStatus,
    EnrollmentStatus,
    SeatClassification,
)
from app.models.master import ApprovalSnapshot, IntakeAllocation
from sqlalchemy import func, select
from sqlalchemy.orm import Session

_COUNTED_ENROLLMENT_STATUSES = {
    EnrollmentStatus.PENDING.value,
    EnrollmentStatus.ACTIVE.value,
    EnrollmentStatus.UNDER_REVIEW.value,
    EnrollmentStatus.TRANSFERRED.value,
}


@dataclass
class CapacityResult:
    programme_id: str
    academic_year: str
    allocations: dict[str, int]
    reported: int
    projected: int
    status: str
    evidence: dict[str, Any] = field(default_factory=dict)
    approval_snapshot_id: str | None = None
    approval_reference: str | None = None

    @property
    def approved_regular(self) -> int:
        return self.allocations.get(SeatClassification.APPROVED_REGULAR.value, 0)

    @property
    def approved_supernumerary(self) -> int:
        return self.allocations.get(SeatClassification.APPROVED_SUPERNUMERARY.value, 0)


def _active_snapshot(db: Session, programme_id: str, academic_year: str) -> ApprovalSnapshot | None:
    return db.scalar(
        select(ApprovalSnapshot)
        .where(
            ApprovalSnapshot.programme_id == programme_id,
            ApprovalSnapshot.academic_year == academic_year,
            ApprovalSnapshot.status == ApprovalSnapshotStatus.ACTIVE.value,
        )
        .order_by(ApprovalSnapshot.version.desc())
    )


def calculate_capacity(
    db: Session,
    programme_id: str,
    academic_year: str,
) -> CapacityResult:
    """Compute reported/projected seats and the explanatory capacity state."""
    snapshot = _active_snapshot(db, programme_id, academic_year)
    if snapshot is None:
        return CapacityResult(
            programme_id=programme_id,
            academic_year=academic_year,
            allocations={
                SeatClassification.APPROVED_REGULAR.value: 0,
                SeatClassification.APPROVED_SUPERNUMERARY.value: 0,
            },
            reported=0,
            projected=0,
            status=CapacityStatus.MISSING_APPROVAL_DATA.value,
            evidence={"reason": "No active approval snapshot for this year"},
        )

    allocations = {
        SeatClassification.APPROVED_REGULAR.value: 0,
        SeatClassification.APPROVED_SUPERNUMERARY.value: 0,
    }
    for allocation in db.scalars(
        select(IntakeAllocation).where(IntakeAllocation.approval_snapshot_id == snapshot.id)
    ).all():
        allocations[allocation.seat_classification] = allocation.approved_count

    reported_by_class = {
        row[0]: int(row[1])
        for row in db.execute(
            select(StudentEnrollment.seat_classification, func.count(StudentEnrollment.id))
            .where(
                StudentEnrollment.programme_id == programme_id,
                StudentEnrollment.academic_year == academic_year,
                StudentEnrollment.is_current.is_(True),
                StudentEnrollment.enrollment_status.in_(_COUNTED_ENROLLMENT_STATUSES),
            )
            .group_by(StudentEnrollment.seat_classification)
        ).all()
    }

    regular = reported_by_class.get(SeatClassification.APPROVED_REGULAR.value, 0)
    supernumerary = reported_by_class.get(SeatClassification.APPROVED_SUPERNUMERARY.value, 0)
    reported = regular + supernumerary
    projected = reported

    approved_regular = allocations[SeatClassification.APPROVED_REGULAR.value]
    approved_super = allocations[SeatClassification.APPROVED_SUPERNUMERARY.value]

    if approved_regular == 0:
        status = CapacityStatus.MISSING_APPROVAL_DATA.value
        reason = "No approved regular allocation"
    elif regular > approved_regular or supernumerary > approved_super:
        status = CapacityStatus.POSSIBLE_EXCESS.value
        reason = (
            "Reported regular or supernumerary enrollment exceeds the approved "
            "allocation for that classification"
        )
    elif supernumerary > 0:
        status = CapacityStatus.WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY.value
        reason = "Within approved regular seats and separately authorized supernumerary seats"
    else:
        status = CapacityStatus.WITHIN_APPROVED_INTAKE.value
        reason = "Within approved regular intake"

    return CapacityResult(
        programme_id=programme_id,
        academic_year=academic_year,
        allocations=allocations,
        reported=reported,
        projected=projected,
        status=status,
        approval_snapshot_id=snapshot.id,
        approval_reference=snapshot.approval_reference,
        evidence={
            "reason": reason,
            "regularReported": regular,
            "supernumeraryReported": supernumerary,
            "regularApproved": approved_regular,
            "supernumeraryApproved": approved_super,
            "snapshotVersion": snapshot.version,
            "allocationRule": "regular and supernumerary capacities are separate",
            "countedStatuses": sorted(_COUNTED_ENROLLMENT_STATUSES),
        },
    )

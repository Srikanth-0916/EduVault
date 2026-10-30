"""Programme and approved-intake master-data endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import CURRENT_ACADEMIC_YEAR
from app.db import get_db
from app.deps import CurrentUser, require_roles
from app.errors import conflict, forbidden, not_found, validation_error
from app.models.enums import ApprovalSnapshotStatus, RecordStatus, SeatClassification
from app.models.master import ApprovalSnapshot, Campus, IntakeAllocation, Programme
from app.schemas.master import (
    AllocationPatch,
    ApprovalSnapshotOut,
    CapacityOut,
    IntakeAllocationOut,
    IntakeSnapshotCreate,
    ProgrammeCreate,
    ProgrammeOut,
)
from app.services.capacity import calculate_capacity
from app.services.master_data import capacity_out, programme_out

router = APIRouter(tags=["programmes"])

_MASTER_ADMIN = require_roles("AICTE_SUPERVISOR", "SYSTEM_ADMIN")


def _get_programme(db: Session, programme_id: str) -> Programme:
    programme = db.get(Programme, programme_id)
    if programme is None:
        raise not_found("Programme not found")
    return programme


def _assert_read(user: CurrentUser, institution_id: str) -> None:
    if user.institution_id is not None and user.institution_id != institution_id:
        raise forbidden()
    # National roles (including analysts) may read aggregate master data.


def _allocation_out(allocation: IntakeAllocation) -> IntakeAllocationOut:
    return IntakeAllocationOut(
        id=allocation.id,
        approval_snapshot_id=allocation.approval_snapshot_id,
        seat_classification=allocation.seat_classification,
        approved_count=allocation.approved_count,
        authorization_reference=allocation.authorization_reference,
    )


def _snapshot_out(db: Session, snapshot: ApprovalSnapshot) -> ApprovalSnapshotOut:
    allocations = db.scalars(
        select(IntakeAllocation)
        .where(IntakeAllocation.approval_snapshot_id == snapshot.id)
        .order_by(IntakeAllocation.seat_classification.asc())
    ).all()
    return ApprovalSnapshotOut(
        id=snapshot.id,
        programme_id=snapshot.programme_id,
        academic_year=snapshot.academic_year,
        approval_reference=snapshot.approval_reference,
        valid_from=snapshot.valid_from,
        valid_to=snapshot.valid_to,
        issued_by=snapshot.issued_by,
        notes=snapshot.notes,
        version=snapshot.version,
        status=snapshot.status,
        allocations=[_allocation_out(item) for item in allocations],
        created_at=snapshot.created_at,
    )


@router.get("/programmes", response_model=list[ProgrammeOut])
def list_programmes(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    institution_id: Annotated[str | None, Query(alias="institutionId")] = None,
    campus_id: Annotated[str | None, Query(alias="campusId")] = None,
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> list[ProgrammeOut]:
    statement = select(Programme)
    if user.institution_id is not None:
        institution_id = user.institution_id
    if institution_id:
        statement = statement.where(Programme.institution_id == institution_id)
    if campus_id:
        statement = statement.where(Programme.campus_id == campus_id)
    programmes = db.scalars(statement.order_by(Programme.programme_name.asc())).all()
    return [programme_out(db, programme, academic_year) for programme in programmes]


@router.get("/programmes/{programme_id}", response_model=ProgrammeOut)
def get_programme(
    programme_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> ProgrammeOut:
    programme = _get_programme(db, programme_id)
    _assert_read(user, programme.institution_id)
    return programme_out(db, programme, academic_year)


@router.post("/campuses/{campus_id}/programmes", response_model=ProgrammeOut, status_code=201)
def create_programme(
    campus_id: str,
    payload: ProgrammeCreate,
    request: Request,
    user: Annotated[object, Depends(_MASTER_ADMIN)],
    db: Annotated[Session, Depends(get_db)],
) -> ProgrammeOut:
    campus = db.get(Campus, campus_id)
    if campus is None:
        raise not_found("Campus not found")

    code = payload.programme_code.strip().upper()
    exists = db.scalar(
        select(Programme).where(
            Programme.campus_id == campus_id,
            func.upper(Programme.programme_code) == code,
        )
    )
    if exists is not None:
        raise conflict("A programme with this code already exists at the campus")

    programme = Programme(
        institution_id=campus.institution_id,
        campus_id=campus.id,
        programme_code=code,
        programme_name=payload.programme_name.strip(),
        award_level=payload.award_level,
        duration_years=payload.duration_years,
        status=RecordStatus.ACTIVE.value,
    )
    db.add(programme)
    db.flush()
    record_audit(
        db,
        actor=user,
        action="PROGRAMME_CREATED",
        resource_type="programme",
        resource_ref=programme.id,
        institution_id=campus.institution_id,
        metadata={"code": code, "campusId": campus.id},
        request=request,
    )
    db.commit()
    return programme_out(db, programme, CURRENT_ACADEMIC_YEAR)


@router.get("/programmes/{programme_id}/intake-snapshots", response_model=list[ApprovalSnapshotOut])
def list_intake_snapshots(
    programme_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[ApprovalSnapshotOut]:
    programme = _get_programme(db, programme_id)
    _assert_read(user, programme.institution_id)
    snapshots = db.scalars(
        select(ApprovalSnapshot)
        .where(ApprovalSnapshot.programme_id == programme_id)
        .order_by(ApprovalSnapshot.academic_year.desc(), ApprovalSnapshot.version.desc())
    ).all()
    return [_snapshot_out(db, snapshot) for snapshot in snapshots]


@router.post(
    "/programmes/{programme_id}/intake-snapshots",
    response_model=ApprovalSnapshotOut,
    status_code=201,
)
def create_intake_snapshot(
    programme_id: str,
    payload: IntakeSnapshotCreate,
    request: Request,
    user: Annotated[object, Depends(_MASTER_ADMIN)],
    db: Annotated[Session, Depends(get_db)],
) -> ApprovalSnapshotOut:
    programme = _get_programme(db, programme_id)
    if payload.valid_to and payload.valid_to < payload.valid_from:
        raise validation_error("validTo must not be before validFrom")

    for allocation in payload.allocations:
        if (
            allocation.seat_classification == SeatClassification.APPROVED_SUPERNUMERARY.value
            and allocation.approved_count > 0
            and not (allocation.authorization_reference or "").strip()
        ):
            raise validation_error(
                "Supernumerary allocations require an authorization reference",
                {"seatClassification": allocation.seat_classification},
            )

    existing = db.scalars(
        select(ApprovalSnapshot).where(
            ApprovalSnapshot.programme_id == programme_id,
            ApprovalSnapshot.academic_year == payload.academic_year,
        )
    ).all()
    for old in existing:
        if old.status == ApprovalSnapshotStatus.ACTIVE.value:
            old.status = ApprovalSnapshotStatus.SUPERSEDED.value
    version = max((item.version for item in existing), default=0) + 1

    snapshot = ApprovalSnapshot(
        programme_id=programme_id,
        academic_year=payload.academic_year,
        approval_reference=payload.approval_reference.strip(),
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        issued_by=payload.issued_by,
        notes=payload.notes,
        version=version,
        status=ApprovalSnapshotStatus.ACTIVE.value,
    )
    db.add(snapshot)
    db.flush()
    for allocation in payload.allocations:
        db.add(
            IntakeAllocation(
                approval_snapshot_id=snapshot.id,
                seat_classification=allocation.seat_classification,
                approved_count=allocation.approved_count,
                authorization_reference=allocation.authorization_reference,
            )
        )
    record_audit(
        db,
        actor=user,
        action="INTAKE_SNAPSHOT_CREATED",
        resource_type="approval_snapshot",
        resource_ref=snapshot.id,
        institution_id=programme.institution_id,
        reason=payload.notes,
        metadata={
            "programmeId": programme_id,
            "academicYear": payload.academic_year,
            "version": version,
        },
        request=request,
    )
    db.commit()
    return _snapshot_out(db, snapshot)


@router.get("/intake", response_model=CapacityOut)
def get_capacity(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    programme_id: Annotated[str, Query(alias="programmeId")],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> CapacityOut:
    programme = _get_programme(db, programme_id)
    _assert_read(user, programme.institution_id)
    return capacity_out(calculate_capacity(db, programme_id, academic_year))


@router.patch("/intake-allocations/{allocation_id}", response_model=IntakeAllocationOut)
def update_allocation(
    allocation_id: str,
    payload: AllocationPatch,
    request: Request,
    user: Annotated[object, Depends(_MASTER_ADMIN)],
    db: Annotated[Session, Depends(get_db)],
) -> IntakeAllocationOut:
    allocation = db.get(IntakeAllocation, allocation_id)
    if allocation is None:
        raise not_found("Intake allocation not found")
    snapshot = db.get(ApprovalSnapshot, allocation.approval_snapshot_id)
    if snapshot is None:
        raise not_found("Approval snapshot not found")
    programme = _get_programme(db, snapshot.programme_id)

    new_count = (
        allocation.approved_count if payload.approved_count is None else payload.approved_count
    )
    new_reference = (
        allocation.authorization_reference
        if payload.authorization_reference is None
        else payload.authorization_reference
    )
    if (
        allocation.seat_classification == SeatClassification.APPROVED_SUPERNUMERARY.value
        and new_count > 0
        and not (new_reference or "").strip()
    ):
        raise validation_error("Supernumerary allocations require an authorization reference")

    before = {
        "approvedCount": allocation.approved_count,
        "authorizationReference": allocation.authorization_reference,
    }
    allocation.approved_count = new_count
    allocation.authorization_reference = new_reference
    if allocation.seat_classification == SeatClassification.APPROVED_REGULAR.value:
        # A regular allocation is the anchor; never allow it to be removed.
        allocation.approved_count = max(0, new_count)
    record_audit(
        db,
        actor=user,
        action="INTAKE_ALLOCATION_UPDATED",
        resource_type="intake_allocation",
        resource_ref=allocation.id,
        institution_id=programme.institution_id,
        reason=payload.reason,
        metadata={"before": before, "after": {"approvedCount": new_count}},
        request=request,
    )
    db.commit()
    return _allocation_out(allocation)

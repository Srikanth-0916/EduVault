"""Shared serializers for master data and capacity views."""

from __future__ import annotations

from app.models.master import Campus, Institution, Programme
from app.schemas.master import (
    CampusOut,
    CapacityOut,
    InstitutionDetail,
    InstitutionOut,
    ProgrammeOut,
)
from app.services.capacity import CapacityResult, calculate_capacity
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def capacity_out(result: CapacityResult) -> CapacityOut:
    return CapacityOut(
        programme_id=result.programme_id,
        academic_year=result.academic_year,
        allocations=result.allocations,
        reported=result.reported,
        projected=result.projected,
        status=result.status,
        evidence=result.evidence,
        approval_snapshot_id=result.approval_snapshot_id,
        approval_reference=result.approval_reference,
    )


def institution_out(db: Session, institution: Institution) -> InstitutionOut:
    campus_count = db.scalar(
        select(func.count(Campus.id)).where(Campus.institution_id == institution.id)
    )
    programme_count = db.scalar(
        select(func.count(Programme.id)).where(Programme.institution_id == institution.id)
    )
    return InstitutionOut(
        id=institution.id,
        aicte_institution_code=institution.aicte_institution_code,
        name=institution.name,
        institution_type=institution.institution_type,
        status=institution.status,
        state=institution.state,
        city=institution.city,
        website_url=institution.website_url,
        contact_email=institution.contact_email,
        campus_count=int(campus_count or 0),
        programme_count=int(programme_count or 0),
    )


def campus_out(campus: Campus) -> CampusOut:
    return CampusOut(
        id=campus.id,
        institution_id=campus.institution_id,
        campus_code=campus.campus_code,
        name=campus.name,
        location=campus.location,
        status=campus.status,
    )


def programme_out(
    db: Session,
    programme: Programme,
    academic_year: str,
    *,
    include_capacity: bool = True,
) -> ProgrammeOut:
    campus = db.get(Campus, programme.campus_id)
    institution = db.get(Institution, programme.institution_id)
    capacity = calculate_capacity(db, programme.id, academic_year) if include_capacity else None
    evidence = capacity.evidence if capacity else {}
    return ProgrammeOut(
        id=programme.id,
        institution_id=programme.institution_id,
        campus_id=programme.campus_id,
        programme_code=programme.programme_code,
        programme_name=programme.programme_name,
        award_level=programme.award_level,
        duration_years=programme.duration_years,
        status=programme.status,
        campus_name=campus.name if campus else None,
        institution_name=institution.name if institution else None,
        approved_regular=int(evidence.get("regularApproved", 0)),
        approved_supernumerary=int(evidence.get("supernumeraryApproved", 0)),
        reported_regular=int(evidence.get("regularReported", 0)),
        reported_supernumerary=int(evidence.get("supernumeraryReported", 0)),
        capacity_status=capacity.status if capacity else None,
        approval_reference=capacity.approval_reference if capacity else None,
    )


def institution_detail(
    db: Session, institution: Institution, academic_year: str
) -> InstitutionDetail:
    summary = institution_out(db, institution)
    campuses = db.scalars(
        select(Campus).where(Campus.institution_id == institution.id).order_by(Campus.name.asc())
    ).all()
    programmes = db.scalars(
        select(Programme)
        .where(Programme.institution_id == institution.id)
        .order_by(Programme.programme_name.asc())
    ).all()
    return InstitutionDetail(
        **summary.model_dump(),
        campuses=[campus_out(campus) for campus in campuses],
        programmes=[programme_out(db, programme, academic_year) for programme in programmes],
    )

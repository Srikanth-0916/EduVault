"""Institution and campus master-data endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.constants import ANALYST_ROLES, CURRENT_ACADEMIC_YEAR, INSTITUTION_TRAVERSAL_ROLES
from app.db import get_db
from app.deps import CurrentUser, Pagination, assert_institution_access, require_roles
from app.errors import conflict, forbidden, not_found
from app.models.enums import InstitutionStatus, RecordStatus
from app.models.master import Campus, Institution, Programme
from app.schemas.common import Page
from app.schemas.master import (
    CampusCreate,
    CampusOut,
    CapacityOut,
    InstitutionCreate,
    InstitutionDetail,
    InstitutionOut,
    ProgrammeOut,
)
from app.services.capacity import calculate_capacity
from app.services.master_data import (
    campus_out,
    capacity_out,
    institution_detail,
    institution_out,
    programme_out,
)

router = APIRouter(prefix="/institutions", tags=["institutions"])

_MASTER_ADMIN = require_roles("AICTE_SUPERVISOR", "SYSTEM_ADMIN")
_READ_NATIONAL = require_roles(*INSTITUTION_TRAVERSAL_ROLES, *ANALYST_ROLES)


def _get_institution(db: Session, institution_id: str) -> Institution:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise not_found("Institution not found")
    return institution


@router.get("/me", response_model=InstitutionDetail)
def get_my_institution(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> InstitutionDetail:
    if not user.institution_id:
        raise forbidden("This account is not institution-scoped")
    institution = _get_institution(db, user.institution_id)
    return institution_detail(db, institution, academic_year)


@router.get("/me/campuses", response_model=list[CampusOut])
def list_my_campuses(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[CampusOut]:
    if not user.institution_id:
        raise forbidden("This account is not institution-scoped")
    campuses = db.scalars(
        select(Campus)
        .where(Campus.institution_id == user.institution_id)
        .order_by(Campus.name.asc())
    ).all()
    return [campus_out(campus) for campus in campuses]


@router.get("/me/programmes", response_model=list[ProgrammeOut])
def list_my_programmes(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> list[ProgrammeOut]:
    if not user.institution_id:
        raise forbidden("This account is not institution-scoped")
    programmes = db.scalars(
        select(Programme)
        .where(Programme.institution_id == user.institution_id)
        .order_by(Programme.programme_name.asc())
    ).all()
    return [
        programme_out(db, programme, academic_year) for programme in programmes
    ]


@router.get("/me/intake", response_model=list[CapacityOut])
def list_my_capacity(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> list[CapacityOut]:
    if not user.institution_id:
        raise forbidden("This account is not institution-scoped")
    programme_ids = db.scalars(
        select(Programme.id)
        .where(Programme.institution_id == user.institution_id)
        .order_by(Programme.programme_name.asc())
    ).all()
    return [
        capacity_out(calculate_capacity(db, programme_id, academic_year))
        for programme_id in programme_ids
    ]


@router.get("", response_model=Page[InstitutionOut])
def list_institutions(
    user: Annotated[object, Depends(_READ_NATIONAL)],
    db: Annotated[Session, Depends(get_db)],
    pagination: Pagination,
    search: str | None = Query(default=None, max_length=120),
) -> Page[InstitutionOut]:
    page, page_size = pagination
    statement = select(Institution)
    count_statement = select(func.count(Institution.id))
    if search:
        term = f"%{search.strip()}%"
        predicate = or_(
            Institution.name.ilike(term),
            Institution.aicte_institution_code.ilike(term),
            Institution.city.ilike(term),
        )
        statement = statement.where(predicate)
        count_statement = count_statement.where(predicate)

    total = int(db.scalar(count_statement) or 0)
    institutions = db.scalars(
        statement.order_by(Institution.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[InstitutionOut](
        items=[institution_out(db, institution) for institution in institutions],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=InstitutionOut, status_code=201)
def create_institution(
    payload: InstitutionCreate,
    request: Request,
    user: Annotated[object, Depends(_MASTER_ADMIN)],
    db: Annotated[Session, Depends(get_db)],
) -> InstitutionOut:
    code = payload.aicte_institution_code.strip().upper()
    exists = db.scalar(
        select(Institution).where(
            func.upper(Institution.aicte_institution_code) == code
        )
    )
    if exists is not None:
        raise conflict("An institution with this AICTE code already exists")

    institution = Institution(
        aicte_institution_code=code,
        name=payload.name.strip(),
        institution_type=payload.institution_type,
        status=InstitutionStatus.ACTIVE.value,
        state=payload.state,
        city=payload.city,
        website_url=payload.website_url,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
    )
    db.add(institution)
    db.flush()
    record_audit(
        db,
        actor=user,
        action="INSTITUTION_CREATED",
        resource_type="institution",
        resource_ref=institution.id,
        metadata={"code": code},
        request=request,
    )
    db.commit()
    return institution_out(db, institution)


@router.get("/{institution_id}/campuses", response_model=list[CampusOut])
def list_campuses(
    institution_id: str,
    user: CurrentUser,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> list[CampusOut]:
    _get_institution(db, institution_id)
    assert_institution_access(db, user, institution_id, request)
    campuses = db.scalars(
        select(Campus)
        .where(Campus.institution_id == institution_id)
        .order_by(Campus.name.asc())
    ).all()
    return [campus_out(campus) for campus in campuses]


@router.get("/{institution_id}", response_model=InstitutionDetail)
def get_institution(
    institution_id: str,
    user: CurrentUser,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> InstitutionDetail:
    institution = _get_institution(db, institution_id)
    assert_institution_access(db, user, institution_id, request)
    return institution_detail(db, institution, academic_year)


@router.post("/{institution_id}/campuses", response_model=CampusOut, status_code=201)
def create_campus(
    institution_id: str,
    payload: CampusCreate,
    request: Request,
    user: Annotated[object, Depends(_MASTER_ADMIN)],
    db: Annotated[Session, Depends(get_db)],
) -> CampusOut:
    _get_institution(db, institution_id)
    code = payload.campus_code.strip().upper()
    exists = db.scalar(
        select(Campus).where(
            Campus.institution_id == institution_id,
            func.upper(Campus.campus_code) == code,
        )
    )
    if exists is not None:
        raise conflict("A campus with this code already exists at the institution")

    campus = Campus(
        institution_id=institution_id,
        campus_code=code,
        name=payload.name.strip(),
        location=payload.location,
        status=RecordStatus.ACTIVE.value,
    )
    db.add(campus)
    db.flush()
    record_audit(
        db,
        actor=user,
        action="CAMPUS_CREATED",
        resource_type="campus",
        resource_ref=campus.id,
        institution_id=institution_id,
        metadata={"code": code},
        request=request,
    )
    db.commit()
    return campus_out(campus)


@router.get("/{institution_id}/programmes", response_model=list[ProgrammeOut])
def list_institution_programmes(
    institution_id: str,
    user: CurrentUser,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> list[ProgrammeOut]:
    _get_institution(db, institution_id)
    assert_institution_access(db, user, institution_id, request)
    programmes = db.scalars(
        select(Programme)
        .where(Programme.institution_id == institution_id)
        .order_by(Programme.programme_name.asc())
    ).all()
    return [
        programme_out(db, programme, academic_year) for programme in programmes
    ]

"""Dashboard endpoints for institution and national views."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import CURRENT_ACADEMIC_YEAR, INSTITUTION_STAFF_ROLES
from app.db import get_db
from app.deps import CurrentUser
from app.errors import forbidden, not_found
from app.models.master import Institution
from app.schemas.dashboard import InstitutionDashboard, NationalDashboard
from app.services.dashboards import institution_dashboard, national_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboards"])


@router.get("/institution", response_model=InstitutionDashboard)
def get_institution_dashboard(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> InstitutionDashboard:
    if not user.institution_id or not set(user.roles) & set(INSTITUTION_STAFF_ROLES):
        raise forbidden("Institution staff access is required")
    institution = db.get(Institution, user.institution_id)
    if institution is None:
        raise not_found("Institution not found")
    return institution_dashboard(db, institution, academic_year)


@router.get("/national", response_model=NationalDashboard)
def get_national_dashboard(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    academic_year: Annotated[str, Query(alias="academicYear")] = CURRENT_ACADEMIC_YEAR,
) -> NationalDashboard:
    if not set(user.roles) & {
        "AICTE_REVIEWER",
        "AICTE_SUPERVISOR",
        "AICTE_ANALYST",
        "SYSTEM_ADMIN",
        "AUDITOR",
    }:
        raise forbidden("AICTE access is required")
    return national_dashboard(db, academic_year)

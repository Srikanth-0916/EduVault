"""Student self-service portal endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import CurrentUser
from app.schemas.verification import StudentMeResponse
from app.services.verification import student_me

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=StudentMeResponse)
def get_student_me(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> StudentMeResponse:
    return student_me(db, user)

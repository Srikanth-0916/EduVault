"""Authenticated consent requests and unauthenticated public verification."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.config import get_settings
from app.db import get_db
from app.deps import CurrentUser
from app.errors import forbidden
from app.schemas.verification import (
    AuthorizeResponse,
    PublicVerificationResponse,
    RevokeRequest,
    VerificationRequestCreate,
    VerificationRequestListResponse,
    VerificationRequestOut,
)
from app.services.verification import (
    _get_request,
    _request_out,
    authorize_request,
    create_request,
    issue_link,
    list_requests,
    resolve_public,
    revoke_request,
)

router = APIRouter(prefix="/verification-requests", tags=["verification"])
public_router = APIRouter(prefix="/public", tags=["public-verification"])
student_router = APIRouter(prefix="/students", tags=["students"])


def _base_url(_request: Request) -> str:
    """Public verifier lives on the web origin, not the API origin."""
    return get_settings().web_base_url.rstrip("/")


@router.post("", response_model=VerificationRequestOut, status_code=201)
def create_verification_request(
    payload: VerificationRequestCreate,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> VerificationRequestOut:
    item = create_request(db, user, payload)
    record_audit(
        db,
        actor=user,
        action="VERIFICATION_REQUEST_CREATED",
        resource_type="verification_request",
        resource_ref=item.id,
        metadata={"claimKeys": payload.requested_claims, "recipientOrg": payload.recipient_org},
        request=request,
    )
    db.commit()
    return _request_out(item)


@router.get("", response_model=VerificationRequestListResponse)
def get_verification_requests(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    scope: Annotated[str, Query()] = "mine",
    status: Annotated[str | None, Query()] = None,
) -> VerificationRequestListResponse:
    items = [_request_out(item) for item in list_requests(db, user, scope, status)]
    return VerificationRequestListResponse(items=items, total=len(items))


@router.get("/{request_id}", response_model=VerificationRequestOut)
def get_verification_request(
    request_id: str,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> VerificationRequestOut:
    item = _get_request(db, request_id)
    if item.subject_user_id != user.id and not set(user.roles) & {
        "AICTE_SUPERVISOR",
        "SYSTEM_ADMIN",
        "AUDITOR",
    }:
        raise forbidden()
    return _request_out(item)


@router.post("/{request_id}/authorize", response_model=AuthorizeResponse)
def authorize_verification_request(
    request_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AuthorizeResponse:
    item = _get_request(db, request_id)
    response = authorize_request(db, item, user, _base_url(request))
    record_audit(
        db,
        actor=user,
        action="VERIFICATION_REQUEST_AUTHORIZED",
        resource_type="verification_request",
        resource_ref=item.id,
        metadata={"mock": True},
        request=request,
    )
    db.commit()
    return response


@router.post("/{request_id}/issue-link", response_model=AuthorizeResponse)
def issue_verification_link(
    request_id: str,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AuthorizeResponse:
    item = _get_request(db, request_id)
    response = issue_link(db, item, user, _base_url(request))
    record_audit(
        db,
        actor=user,
        action="VERIFICATION_LINK_ISSUED",
        resource_type="verification_request",
        resource_ref=item.id,
        request=request,
    )
    db.commit()
    return response


@router.post("/{request_id}/revoke", response_model=VerificationRequestOut)
def revoke_verification_request(
    request_id: str,
    payload: RevokeRequest,
    request: Request,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> VerificationRequestOut:
    item = _get_request(db, request_id)
    revoke_request(db, item, user, payload.reason)
    record_audit(
        db,
        actor=user,
        action="VERIFICATION_REQUEST_REVOKED",
        resource_type="verification_request",
        resource_ref=item.id,
        reason=payload.reason,
        request=request,
    )
    db.commit()
    return _request_out(item)


@public_router.get("/verify/{token}", response_model=PublicVerificationResponse)
def public_verify(
    token: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> PublicVerificationResponse:
    client_ip = request.client.host if request.client else None
    return resolve_public(
        db,
        token,
        request_meta={
            "ipAddress": client_ip,
            "userAgent": request.headers.get("user-agent"),
            "traceId": getattr(request.state, "trace_id", None),
        },
    )


__all__ = ["public_router", "router", "student_router"]

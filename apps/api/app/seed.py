"""Deterministic synthetic seed data.

Run with::

    uv run python -m app.seed --reset

The seed is idempotent when the primary demo institution already exists. All
values are fictional; ``Demo@1234`` is a public demo password.
"""

from __future__ import annotations

import argparse
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.constants import (
    CAMPUS_IDS,
    DEMO_PASSWORD,
    INSTITUTION_IDS,
    PROGRAMME_IDS,
    STUDENT_IDENTITY_ID,
    USER_IDS,
)
from app.db import create_all, drop_all, get_session_factory
from app.models.enums import (
    ApprovalSnapshotStatus,
    AwardLevel,
    IdentityStatus,
    InstitutionStatus,
    InstitutionType,
    MembershipScope,
    RecordStatus,
    SeatClassification,
    UserRole,
    UserStatus,
)
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
from app.security import apaar_key_id, apaar_lookup_token, encrypt_apaar, hash_password


def _membership(
    *,
    user_id: str,
    role: UserRole,
    institution_id: str | None,
    scope: MembershipScope,
) -> OrganizationMembership:
    return OrganizationMembership(
        user_id=user_id,
        institution_id=institution_id,
        role=role.value,
        scope=scope.value,
        valid_from=date(2025, 1, 1),
        is_active=True,
    )


def seed_core(db: Session) -> dict[str, int]:
    """Insert the core demo dataset into an existing schema/session."""
    if db.get(Institution, INSTITUTION_IDS["AIT"]) is not None:
        return {
            "institutions": db.query(Institution).count(),
            "programmes": db.query(Programme).count(),
            "users": db.query(User).count(),
        }

    institutions = [
        Institution(
            id=INSTITUTION_IDS["AIT"],
            aicte_institution_code="AICTE-DEMO-AIT",
            name="Aarav Institute of Technology (Demo)",
            institution_type=InstitutionType.PRIVATE_SELF_FINANCED.value,
            status=InstitutionStatus.ACTIVE.value,
            state="Maharashtra",
            city="Pune",
            website_url="https://demo-ait.example",
            contact_email="office@demo-ait.edu",
        ),
        Institution(
            id=INSTITUTION_IDS["BIE"],
            aicte_institution_code="AICTE-DEMO-BIE",
            name="Bharat Institute of Engineering (Demo)",
            institution_type=InstitutionType.GOVERNMENT.value,
            status=InstitutionStatus.ACTIVE.value,
            state="Karnataka",
            city="Bengaluru",
            website_url="https://demo-bie.example",
            contact_email="office@demo-bie.edu",
        ),
        Institution(
            id=INSTITUTION_IDS["CIM"],
            aicte_institution_code="AICTE-DEMO-CIM",
            name="Chitra Institute of Management (Demo)",
            institution_type=InstitutionType.PRIVATE_SELF_FINANCED.value,
            status=InstitutionStatus.ACTIVE.value,
            state="Tamil Nadu",
            city="Chennai",
            website_url="https://demo-cim.example",
            contact_email="office@demo-cim.edu",
        ),
    ]
    db.add_all(institutions)
    db.flush()

    campuses = [
        Campus(
            id=CAMPUS_IDS["AIT"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_code="AIT-MAIN",
            name="Aarav Main Campus",
            location="Pune, Maharashtra",
            status=RecordStatus.ACTIVE.value,
        ),
        Campus(
            id=CAMPUS_IDS["BIE"],
            institution_id=INSTITUTION_IDS["BIE"],
            campus_code="BIE-MAIN",
            name="Bharat Main Campus",
            location="Bengaluru, Karnataka",
            status=RecordStatus.ACTIVE.value,
        ),
        Campus(
            id=CAMPUS_IDS["CIM"],
            institution_id=INSTITUTION_IDS["CIM"],
            campus_code="CIM-MAIN",
            name="Chitra Main Campus",
            location="Chennai, Tamil Nadu",
            status=RecordStatus.ACTIVE.value,
        ),
    ]
    db.add_all(campuses)
    db.flush()

    programmes = [
        Programme(
            id=PROGRAMME_IDS["AIT_CSE"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_id=CAMPUS_IDS["AIT"],
            programme_code="CSE",
            programme_name="B.Tech Computer Science and Engineering",
            award_level=AwardLevel.UNDERGRADUATE.value,
            duration_years=4,
            status=RecordStatus.ACTIVE.value,
        ),
        Programme(
            id=PROGRAMME_IDS["AIT_ECE"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_id=CAMPUS_IDS["AIT"],
            programme_code="ECE",
            programme_name="B.Tech Electronics and Communication Engineering",
            award_level=AwardLevel.UNDERGRADUATE.value,
            duration_years=4,
            status=RecordStatus.ACTIVE.value,
        ),
        Programme(
            id=PROGRAMME_IDS["BIE_MECH"],
            institution_id=INSTITUTION_IDS["BIE"],
            campus_id=CAMPUS_IDS["BIE"],
            programme_code="MECH",
            programme_name="B.Tech Mechanical Engineering",
            award_level=AwardLevel.UNDERGRADUATE.value,
            duration_years=4,
            status=RecordStatus.ACTIVE.value,
        ),
        Programme(
            id=PROGRAMME_IDS["CIM_MBA"],
            institution_id=INSTITUTION_IDS["CIM"],
            campus_id=CAMPUS_IDS["CIM"],
            programme_code="MBA",
            programme_name="Master of Business Administration",
            award_level=AwardLevel.POSTGRADUATE.value,
            duration_years=2,
            status=RecordStatus.ACTIVE.value,
        ),
    ]
    db.add_all(programmes)
    db.flush()

    snapshot_specs: list[tuple[str, str, int, int, int]] = [
        # programme key, short code, regular, supernumerary, year start
        ("AIT_CSE", "AIT-CSE", 120, 12, 2026),
        ("AIT_ECE", "AIT-ECE", 60, 6, 2026),
        ("BIE_MECH", "BIE-MECH", 90, 0, 2026),
        ("CIM_MBA", "CIM-MBA", 60, 0, 2026),
    ]
    for key, short, regular, supernumerary, year_start in snapshot_specs:
        for offset, academic_year in enumerate(("2025-26", "2026-27")):
            snapshot_id = f"appr_{key.lower()}_{academic_year.replace('-', '_')}"
            snapshot = ApprovalSnapshot(
                id=snapshot_id,
                programme_id=PROGRAMME_IDS[key],
                academic_year=academic_year,
                approval_reference=f"AICTE/APPR/{academic_year}/{short}",
                valid_from=date(year_start + offset - 1, 6, 1),
                valid_to=None,
                issued_by="AICTE (Demo)",
                notes="Synthetic approval snapshot for demonstration only.",
                version=1,
                status=ApprovalSnapshotStatus.ACTIVE.value,
            )
            db.add(snapshot)
            db.flush()
            regular_count = regular if offset else max(1, regular - 10)
            db.add(
                IntakeAllocation(
                    approval_snapshot_id=snapshot.id,
                    seat_classification=SeatClassification.APPROVED_REGULAR.value,
                    approved_count=regular_count,
                )
            )
            if supernumerary:
                db.add(
                    IntakeAllocation(
                        approval_snapshot_id=snapshot.id,
                        seat_classification=SeatClassification.APPROVED_SUPERNUMERARY.value,
                        approved_count=supernumerary,
                        authorization_reference=f"AICTE/SN/{academic_year}/{short}",
                    )
                )

    identity = StudentIdentity(
        id=STUDENT_IDENTITY_ID,
        apaar_ciphertext=encrypt_apaar("123456789012"),
        apaar_lookup_token=apaar_lookup_token("123456789012"),
        apaar_last4="9012",
        identifier_status=IdentityStatus.FORMAT_VALID.value,
        key_id=apaar_key_id(),
    )
    db.add(identity)

    password_hash = hash_password(DEMO_PASSWORD)
    users: list[tuple[str, str, str]] = [
        (USER_IDS["ait_admin"], "admin@demo-ait.edu", "Aarav Admin"),
        (USER_IDS["ait_operator"], "operator@demo-ait.edu", "Arjun Nair"),
        (USER_IDS["ait_nodal"], "nodal@demo-ait.edu", "Nisha Kulkarni"),
        (USER_IDS["ait_student"], "student@demo-ait.edu", "Synthetic Student One"),
        (USER_IDS["reviewer"], "reviewer@aicte.demo", "Riya Reviewer"),
        (USER_IDS["supervisor"], "supervisor@aicte.demo", "Sam Supervisor"),
        (USER_IDS["analyst"], "analyst@aicte.demo", "Anita Analyst"),
        (USER_IDS["sysadmin"], "sysadmin@aicte.demo", "Sid System"),
        (USER_IDS["auditor"], "auditor@aicte.demo", "Aarav Auditor"),
        (USER_IDS["verifier"], "verifier@acme-demo.example", "Vera Verifier"),
    ]
    for user_id, email, full_name in users:
        db.add(
            User(
                id=user_id,
                email=email,
                full_name=full_name,
                hashed_password=password_hash,
                status=UserStatus.ACTIVE.value,
            )
        )
    db.flush()

    # The student user is linked to one protected identity.
    student = db.get(User, USER_IDS["ait_student"])
    assert student is not None
    student.student_identity_id = identity.id

    memberships: list[tuple[str, UserRole, str | None, MembershipScope]] = [
        (
            USER_IDS["ait_admin"],
            UserRole.INSTITUTION_ADMIN,
            INSTITUTION_IDS["AIT"],
            MembershipScope.INSTITUTION,
        ),
        (
            USER_IDS["ait_operator"],
            UserRole.INSTITUTION_OPERATOR,
            INSTITUTION_IDS["AIT"],
            MembershipScope.INSTITUTION,
        ),
        (
            USER_IDS["ait_nodal"],
            UserRole.INSTITUTION_NODAL_OFFICER,
            INSTITUTION_IDS["AIT"],
            MembershipScope.INSTITUTION,
        ),
        (
            USER_IDS["ait_student"],
            UserRole.STUDENT,
            INSTITUTION_IDS["AIT"],
            MembershipScope.INSTITUTION,
        ),
        (USER_IDS["reviewer"], UserRole.AICTE_REVIEWER, None, MembershipScope.NATIONAL),
        (
            USER_IDS["supervisor"],
            UserRole.AICTE_SUPERVISOR,
            None,
            MembershipScope.NATIONAL,
        ),
        (USER_IDS["analyst"], UserRole.AICTE_ANALYST, None, MembershipScope.NATIONAL),
        (USER_IDS["sysadmin"], UserRole.SYSTEM_ADMIN, None, MembershipScope.NATIONAL),
        (USER_IDS["auditor"], UserRole.AUDITOR, None, MembershipScope.NATIONAL),
        (
            USER_IDS["verifier"],
            UserRole.EXTERNAL_VERIFIER,
            None,
            MembershipScope.NATIONAL,
        ),
    ]
    for user_id, role, institution_id, scope in memberships:
        db.add(
            _membership(
                user_id=user_id,
                role=role,
                institution_id=institution_id,
                scope=scope,
            )
        )

    db.flush()
    return {
        "institutions": len(institutions),
        "campuses": len(campuses),
        "programmes": len(programmes),
        "approval_snapshots": len(snapshot_specs) * 2,
        "users": len(users),
        "memberships": len(memberships),
    }


def seed(*, reset: bool = False, session: Session | None = None) -> dict[str, Any]:
    """Seed the database. With ``reset`` the prototype schema is recreated."""
    if reset:
        drop_all()
        create_all()
    if session is not None:
        counts = seed_core(session)
        session.flush()
        return counts
    with get_session_factory()() as db:
        counts = seed_core(db)
        db.commit()
        return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed APAAR-SDMV synthetic demo data")
    parser.add_argument("--reset", action="store_true", help="drop and recreate prototype tables")
    args = parser.parse_args()
    counts = seed(reset=args.reset)
    summary = ", ".join(f"{key}={value}" for key, value in counts.items())
    print(f"Seeded demo data: {summary}")


if __name__ == "__main__":
    main()

"""Deterministic synthetic seed data.

Run with::

    uv run python -m app.seed --reset

The seed is idempotent when the primary demo institution already exists. All
values are fictional; ``Demo@1234`` is a public demo password.
"""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime
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
from app.models.enrollment import EnrollmentVersion, StudentEnrollment
from app.models.enums import (
    ApprovalSnapshotStatus,
    AwardLevel,
    DeclaredStatus,
    EnrollmentStatus,
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
from app.security import (
    apaar_key_id,
    apaar_lookup_token,
    encrypt_apaar,
    hash_password,
    mask_apaar,
)
from app.services.apaar import upsert_student_identity


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


_FIRST_NAMES = [
    "Aarav", "Ananya", "Bhavya", "Chirag", "Devika", "Eshan", "Farah", "Gaurav",
    "Harini", "Ishaan", "Jaya", "Kabir", "Lakshmi", "Mihir", "Neha", "Omkar",
    "Pooja", "Rohan", "Sanya", "Tanvi", "Uday", "Veda", "Yash", "Zoya",
]
_LAST_NAMES = [
    "Agarwal", "Bhat", "Chandra", "Desai", "Ezhil", "Fernandes", "Ghosh",
    "Hegde", "Iyer", "Jain", "Kapoor", "Lal", "Mehta", "Nair", "Oberoi",
    "Patel", "Qureshi", "Rao", "Shah", "Tiwari", "Usman", "Verma", "Yadav",
    "Zachariah",
]


def _seed_enrollments(db: Session) -> dict[str, int]:
    """Create 90 deterministic, current enrolment snapshots for demos.

    The set deliberately includes same-institution duplicates, a cross-
    institution overlap, a valid non-overlapping transfer, malformed/missing
    identifiers, supernumerary allocations with and without a reference, and
    one over-intake programme. Raw APAAR values live only in this local list and
    are encrypted before insert.
    """
    schedule: list[tuple[str, str, str, str, int]] = [
        # programme key, campus key, local code, programme code, count
        ("AIT_CSE", "AIT", "AIT", "CSE", 24),
        ("AIT_ECE", "AIT", "AIT", "ECE", 18),
        ("AIT_AIML", "AIT_NORTH", "AITN", "AIML", 12),
        ("AIT_MECH", "AIT_NORTH", "AITN", "MECH", 10),
        ("BIE_MECH", "BIE", "BIE", "MECH", 8),
        ("BIE_CIVIL", "BIE_CITY", "BIEC", "CIVIL", 6),
        ("CIM_MBA", "CIM", "CIM", "MBA", 8),
        ("CIM_BBA", "CIM", "CIM", "BBA", 4),
    ]

    rows: list[dict[str, Any]] = []
    for programme_key, campus_key, local_prefix, programme_code, count in schedule:
        for local_index in range(count):
            index = len(rows)
            if index == 0:
                name = "Synthetic Student One"
            else:
                name = (
                    f"{_FIRST_NAMES[index % len(_FIRST_NAMES)]} "
                    f"{_LAST_NAMES[(index * 7) % len(_LAST_NAMES)]}"
                )
            rows.append(
                {
                    "index": index,
                    "programme_key": programme_key,
                    "campus_key": campus_key,
                    "programme_code": programme_code,
                    "local_prefix": local_prefix,
                    "local_index": local_index + 1,
                    "name": name,
                    "raw_apaar": f"{700000000000 + index:012d}",
                    "identity_status": IdentityStatus.FORMAT_VALID.value,
                    "academic_year": "2026-27",
                    "admission_date": date(2026, 7, 15),
                    "exit_date": None,
                    "enrollment_status": EnrollmentStatus.ACTIVE.value,
                    "seat_classification": SeatClassification.APPROVED_REGULAR.value,
                    "supernumerary_ref": None,
                    "nri": DeclaredStatus.UNKNOWN.value,
                    "oci": DeclaredStatus.UNKNOWN.value,
                    "foreign": DeclaredStatus.UNKNOWN.value,
                }
            )

    assert len(rows) == 90

    # Protected student account: same identity as the first AIT CSE enrollment.
    rows[0]["raw_apaar"] = "123456789012"

    # Same-institution duplicate pair (overlapping current records).
    rows[1]["raw_apaar"] = rows[0]["raw_apaar"]
    rows[1]["name"] = rows[0]["name"]

    # Missing/malformed identities must remain visibly unverified.
    rows[2]["raw_apaar"] = "ABC123"
    rows[2]["identity_status"] = IdentityStatus.MALFORMED.value
    rows[2]["enrollment_status"] = EnrollmentStatus.PENDING.value
    rows[3]["raw_apaar"] = ""
    rows[3]["identity_status"] = IdentityStatus.MISSING.value
    rows[3]["enrollment_status"] = EnrollmentStatus.PENDING.value

    # Supernumerary capacity: one with an authorization reference, one without.
    rows[4]["seat_classification"] = SeatClassification.APPROVED_SUPERNUMERARY.value
    rows[4]["supernumerary_ref"] = "AICTE/SN/2026-27/AIT-CSE"
    rows[5]["seat_classification"] = SeatClassification.APPROVED_SUPERNUMERARY.value

    # Deterministic mock-adapter outcomes for the demo.
    rows[24]["raw_apaar"] = "700000000099"
    rows[24]["identity_status"] = IdentityStatus.PENDING_EXTERNAL_CHECK.value
    rows[25]["raw_apaar"] = "700000000088"
    rows[25]["identity_status"] = IdentityStatus.PENDING_EXTERNAL_CHECK.value

    # Same person at two institutions with overlapping dates.
    rows[64]["raw_apaar"] = rows[42]["raw_apaar"]
    rows[64]["name"] = rows[42]["name"]

    # Non-overlapping transfer pair: BIE first, then AIT.
    rows[54]["raw_apaar"] = "700000000054"
    rows[54]["academic_year"] = "2025-26"
    rows[54]["admission_date"] = date(2025, 7, 15)
    rows[72]["raw_apaar"] = rows[54]["raw_apaar"]
    rows[72]["name"] = rows[54]["name"]
    rows[72]["academic_year"] = "2025-26"
    rows[72]["admission_date"] = date(2024, 7, 15)
    rows[72]["exit_date"] = date(2025, 6, 30)
    rows[72]["enrollment_status"] = EnrollmentStatus.TRANSFERRED.value

    rows[7]["nri"] = DeclaredStatus.YES.value
    rows[8]["oci"] = DeclaredStatus.YES.value
    rows[9]["foreign"] = DeclaredStatus.YES.value

    programme_to_campus = {
        key: CAMPUS_IDS[campus_key]
        for key, campus_key, _, _, _ in schedule
    }
    programme_index: dict[str, int] = {}
    accepted_at = datetime(2026, 8, 1, tzinfo=UTC)
    transfer_accepted_at = datetime(2025, 9, 1, tzinfo=UTC)

    for row in rows:
        programme_key = str(row["programme_key"])
        programme_index[programme_key] = programme_index.get(programme_key, 0) + 1
        academic_year = str(row["academic_year"])
        local_id = (
            f"{row['local_prefix']}{academic_year.replace('-', '')}"
            f"{row['programme_code']}{row['local_index']:03d}"
        )
        raw = str(row["raw_apaar"])
        identity = upsert_student_identity(
            db, raw or None, str(row["identity_status"])
        )
        identity.identifier_status = str(row["identity_status"])
        if raw and len(raw) == 12 and raw.isdigit():
            identity.apaar_last4 = raw[-4:]
        enrollment_id = f"enr_{programme_key.lower()}_{programme_index[programme_key]:03d}"
        enrollment = StudentEnrollment(
            id=enrollment_id,
            student_identity_id=identity.id,
            institution_id=INSTITUTION_IDS[
                "AIT"
                if programme_key.startswith("AIT")
                else "BIE"
                if programme_key.startswith("BIE")
                else "CIM"
            ],
            campus_id=programme_to_campus[programme_key],
            programme_id=PROGRAMME_IDS[programme_key],
            student_local_id=local_id,
            student_full_name=str(row["name"]),
            academic_year=academic_year,
            admission_date=row["admission_date"],
            exit_date=row["exit_date"],
            enrollment_status=str(row["enrollment_status"]),
            seat_classification=str(row["seat_classification"]),
            admission_category="GENERAL",
            nri_status=str(row["nri"]),
            oci_status=str(row["oci"]),
            foreign_national_status=str(row["foreign"]),
            supernumerary_approval_reference=row["supernumerary_ref"],
            version=1,
            is_current=True,
            supersedes_id=None,
            correction_reason=None,
            source_channel="SEED",
            created_by=USER_IDS["ait_admin"],
            updated_by=USER_IDS["ait_admin"],
            record_accepted_at=(
                transfer_accepted_at
                if academic_year == "2025-26"
                else accepted_at
                if row["enrollment_status"] == EnrollmentStatus.ACTIVE.value
                else None
            ),
        )
        db.add(enrollment)
        db.flush()
        db.add(
            EnrollmentVersion(
                student_enrollment_id=enrollment.id,
                version=1,
                snapshot={
                    "studentLocalId": local_id,
                    "studentName": row["name"],
                    "maskedApaar": mask_apaar(raw) if raw else mask_apaar(None),
                    "identityStatus": identity.identifier_status,
                    "programmeId": PROGRAMME_IDS[programme_key],
                    "campusId": programme_to_campus[programme_key],
                    "academicYear": academic_year,
                    "enrollmentStatus": row["enrollment_status"],
                    "seatClassification": row["seat_classification"],
                    "version": 1,
                },
                change_reason="Synthetic seed snapshot",
                changed_by=USER_IDS["ait_admin"],
                actor_role=UserRole.SYSTEM_ADMIN.value,
            )
        )

    db.flush()
    return {
        "student_identities": db.query(StudentIdentity).count(),
        "enrollments": len(rows),
        "enrollment_versions": db.query(EnrollmentVersion).count(),
    }


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
            id=CAMPUS_IDS["AIT_NORTH"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_code="AIT-NORTH",
            name="Aarav North Campus",
            location="Pimpri, Maharashtra",
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
            id=CAMPUS_IDS["BIE_CITY"],
            institution_id=INSTITUTION_IDS["BIE"],
            campus_code="BIE-CITY",
            name="Bharat City Campus",
            location="Mysuru, Karnataka",
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
            id=PROGRAMME_IDS["AIT_AIML"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_id=CAMPUS_IDS["AIT_NORTH"],
            programme_code="AIML",
            programme_name="B.Tech Artificial Intelligence and Machine Learning",
            award_level=AwardLevel.UNDERGRADUATE.value,
            duration_years=4,
            status=RecordStatus.ACTIVE.value,
        ),
        Programme(
            id=PROGRAMME_IDS["AIT_MECH"],
            institution_id=INSTITUTION_IDS["AIT"],
            campus_id=CAMPUS_IDS["AIT_NORTH"],
            programme_code="MECH",
            programme_name="B.Tech Mechanical Engineering",
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
            id=PROGRAMME_IDS["BIE_CIVIL"],
            institution_id=INSTITUTION_IDS["BIE"],
            campus_id=CAMPUS_IDS["BIE_CITY"],
            programme_code="CIVIL",
            programme_name="B.Tech Civil Engineering",
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
        Programme(
            id=PROGRAMME_IDS["CIM_BBA"],
            institution_id=INSTITUTION_IDS["CIM"],
            campus_id=CAMPUS_IDS["CIM"],
            programme_code="BBA",
            programme_name="Bachelor of Business Administration",
            award_level=AwardLevel.UNDERGRADUATE.value,
            duration_years=3,
            status=RecordStatus.ACTIVE.value,
        ),
    ]
    db.add_all(programmes)
    db.flush()

    snapshot_specs: list[tuple[str, str, int, int, int]] = [
        # programme key, short code, regular, supernumerary, year start
        ("AIT_CSE", "AIT-CSE", 120, 12, 2026),
        ("AIT_ECE", "AIT-ECE", 60, 6, 2026),
        ("AIT_AIML", "AIT-AIML", 60, 6, 2026),
        ("AIT_MECH", "AIT-MECH", 60, 0, 2026),
        ("BIE_MECH", "BIE-MECH", 90, 0, 2026),
        ("BIE_CIVIL", "BIE-CIVIL", 60, 0, 2026),
        ("CIM_MBA", "CIM-MBA", 60, 0, 2026),
        ("CIM_BBA", "CIM-BBA", 3, 0, 2026),
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
            suffix = "" if offset else "_2025"
            db.add(
                IntakeAllocation(
                    id=f"alloc_{key.lower()}_regular{suffix}",
                    approval_snapshot_id=snapshot.id,
                    seat_classification=SeatClassification.APPROVED_REGULAR.value,
                    approved_count=regular_count,
                )
            )
            if supernumerary:
                db.add(
                    IntakeAllocation(
                        id=f"alloc_{key.lower()}_supernumerary{suffix}",
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
    enrollment_counts = _seed_enrollments(db)
    db.flush()
    return {
        "institutions": len(institutions),
        "campuses": len(campuses),
        "programmes": len(programmes),
        "approval_snapshots": len(snapshot_specs) * 2,
        "users": len(users),
        "memberships": len(memberships),
        **enrollment_counts,
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

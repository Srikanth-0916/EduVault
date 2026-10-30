"""Canonical constants shared by seed data, authorization, and tests.

All demo values are synthetic. The password below is intentionally public and
must never be used outside the demo.
"""

from __future__ import annotations

DEMO_PASSWORD = "Demo@1234"

ACADEMIC_YEARS = ("2025-26", "2026-27")
CURRENT_ACADEMIC_YEAR = "2026-27"

INSTITUTION_ROLES = (
    "INSTITUTION_ADMIN",
    "INSTITUTION_OPERATOR",
    "INSTITUTION_NODAL_OFFICER",
    "STUDENT",
)
INSTITUTION_STAFF_ROLES = (
    "INSTITUTION_ADMIN",
    "INSTITUTION_OPERATOR",
    "INSTITUTION_NODAL_OFFICER",
)
NATIONAL_ROLES = (
    "AICTE_REVIEWER",
    "AICTE_SUPERVISOR",
    "AICTE_ANALYST",
    "SYSTEM_ADMIN",
    "AUDITOR",
    "EXTERNAL_VERIFIER",
)
ALL_ROLES = (*INSTITUTION_ROLES, *NATIONAL_ROLES)

# Reviewers/supervisors/auditors/system admins may traverse institution scopes.
# Analysts are handled separately because their access is aggregate-only.
INSTITUTION_TRAVERSAL_ROLES = (
    "AICTE_REVIEWER",
    "AICTE_SUPERVISOR",
    "AUDITOR",
    "SYSTEM_ADMIN",
)
ANALYST_ROLES = ("AICTE_ANALYST",)

ROLE_LABELS = {
    "INSTITUTION_ADMIN": "Institution administrator",
    "INSTITUTION_OPERATOR": "Institution operator",
    "INSTITUTION_NODAL_OFFICER": "Nodal officer",
    "AICTE_REVIEWER": "AICTE reviewer",
    "AICTE_SUPERVISOR": "AICTE supervisor",
    "AICTE_ANALYST": "AICTE analyst",
    "SYSTEM_ADMIN": "System administrator",
    "AUDITOR": "Auditor",
    "STUDENT": "Student",
    "EXTERNAL_VERIFIER": "External verifier",
}

# Stable IDs used by the seed and demo scenarios.
INSTITUTION_IDS = {
    "AIT": "inst_ait",
    "BIE": "inst_bie",
    "CIM": "inst_cim",
}
CAMPUS_IDS = {
    "AIT": "camp_ait_main",
    "AIT_NORTH": "camp_ait_north",
    "BIE": "camp_bie_main",
    "BIE_CITY": "camp_bie_city",
    "CIM": "camp_cim_main",
}
PROGRAMME_IDS = {
    "AIT_CSE": "prog_ait_cse",
    "AIT_ECE": "prog_ait_ece",
    "AIT_AIML": "prog_ait_aiml",
    "AIT_MECH": "prog_ait_mech",
    "BIE_MECH": "prog_bie_mech",
    "BIE_CIVIL": "prog_bie_civil",
    "CIM_MBA": "prog_cim_mba",
    "CIM_BBA": "prog_cim_bba",
}
USER_IDS = {
    "ait_admin": "usr_ait_admin",
    "ait_operator": "usr_ait_operator",
    "ait_nodal": "usr_ait_nodal",
    "ait_student": "usr_ait_student",
    "reviewer": "usr_aicte_reviewer",
    "supervisor": "usr_aicte_supervisor",
    "analyst": "usr_aicte_analyst",
    "sysadmin": "usr_sysadmin",
    "auditor": "usr_auditor",
    "verifier": "usr_external_verifier",
}
STUDENT_IDENTITY_ID = "sid_demo_student_1"

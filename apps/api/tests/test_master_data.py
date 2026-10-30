"""Master data, approved intake, and tenant isolation tests."""

from __future__ import annotations

from tests.factories import auth_headers


def test_seed_master_data_and_enrollment_counts(client, seeded) -> None:
    headers = auth_headers(client, "reviewer@aicte.demo")
    institutions = client.get("/api/v1/institutions?pageSize=10", headers=headers)
    assert institutions.status_code == 200
    body = institutions.json()
    assert body["total"] == 3
    assert {item["id"] for item in body["items"]} == {"inst_ait", "inst_bie", "inst_cim"}

    detail = client.get("/api/v1/institutions/inst_ait", headers=headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert len(payload["campuses"]) == 2
    assert len(payload["programmes"]) == 4
    assert payload["programmes"][0]["approvedRegular"] >= 0


def test_institution_me_is_tenant_scoped(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.get("/api/v1/institutions/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == "inst_ait"
    assert {campus["campusCode"] for campus in response.json()["campuses"]} == {
        "AIT-MAIN",
        "AIT-NORTH",
    }

    cross_tenant = client.get("/api/v1/institutions/inst_bie", headers=headers)
    assert cross_tenant.status_code == 403
    assert cross_tenant.json()["error"]["code"] == "FORBIDDEN"


def test_institution_cannot_edit_intake(client, seeded) -> None:
    headers = auth_headers(client, "admin@demo-ait.edu")
    response = client.patch(
        "/api/v1/intake-allocations/alloc_ait_cse_regular",
        json={"approvedCount": 500},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_supervisor_can_edit_intake_and_capacity_reflects_it(client, seeded) -> None:
    headers = auth_headers(client, "supervisor@aicte.demo")
    response = client.patch(
        "/api/v1/intake-allocations/alloc_ait_cse_regular",
        json={"approvedCount": 150, "reason": "Corrected approved intake"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["approvedCount"] == 150

    capacity = client.get(
        "/api/v1/intake?programmeId=prog_ait_cse&academicYear=2026-27",
        headers=headers,
    )
    assert capacity.status_code == 200
    assert capacity.json()["allocations"]["APPROVED_REGULAR"] == 150


def test_capacity_supernumerary_separate(client, seeded) -> None:
    headers = auth_headers(client, "reviewer@aicte.demo")
    data = client.get(
        "/api/v1/intake?programmeId=prog_ait_cse&academicYear=2026-27",
        headers=headers,
    ).json()
    assert data["allocations"]["APPROVED_REGULAR"] >= 1
    assert data["allocations"]["APPROVED_SUPERNUMERARY"] >= 1
    assert data["status"] == "WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY"


def test_master_data_create_flow_requires_national_roles(client, seeded) -> None:
    operator = auth_headers(client, "operator@demo-ait.edu")
    forbidden = client.post(
        "/api/v1/institutions",
        json={
            "aicteInstitutionCode": "AICTE-DEMO-XYZ",
            "name": "Unauthorized Institute (Demo)",
            "institutionType": "PRIVATE_SELF_FINANCED",
        },
        headers=operator,
    )
    assert forbidden.status_code == 403

    supervisor = auth_headers(client, "supervisor@aicte.demo")
    created = client.post(
        "/api/v1/institutions",
        json={
            "aicteInstitutionCode": "AICTE-DEMO-XYZ",
            "name": "Demo Test Institute (Demo)",
            "institutionType": "PRIVATE_SELF_FINANCED",
            "state": "Gujarat",
            "city": "Ahmedabad",
        },
        headers=supervisor,
    )
    assert created.status_code == 201, created.text
    institution_id = created.json()["id"]

    campus = client.post(
        f"/api/v1/institutions/{institution_id}/campuses",
        json={"campusCode": "XYZ-MAIN", "name": "Demo Test Campus"},
        headers=supervisor,
    )
    assert campus.status_code == 201, campus.text
    campus_id = campus.json()["id"]

    programme = client.post(
        f"/api/v1/campuses/{campus_id}/programmes",
        json={
            "programmeCode": "CSE",
            "programmeName": "B.Tech Computer Science and Engineering",
            "awardLevel": "UNDERGRADUATE",
            "durationYears": 4,
        },
        headers=supervisor,
    )
    assert programme.status_code == 201, programme.text
    programme_id = programme.json()["id"]

    snapshot = client.post(
        f"/api/v1/programmes/{programme_id}/intake-snapshots",
        json={
            "academicYear": "2026-27",
            "approvalReference": "AICTE/APPR/2026-27/XYZ-CSE",
            "validFrom": "2026-06-01",
            "allocations": [
                {"seatClassification": "APPROVED_REGULAR", "approvedCount": 40},
                {
                    "seatClassification": "APPROVED_SUPERNUMERARY",
                    "approvedCount": 4,
                    "authorizationReference": "AICTE/SN/2026-27/XYZ",
                },
            ],
        },
        headers=supervisor,
    )
    assert snapshot.status_code == 201, snapshot.text
    assert snapshot.json()["version"] == 1
    assert len(snapshot.json()["allocations"]) == 2

    revised = client.post(
        f"/api/v1/programmes/{programme_id}/intake-snapshots",
        json={
            "academicYear": "2026-27",
            "approvalReference": "AICTE/APPR/2026-27/XYZ-CSE-REV",
            "validFrom": "2026-06-01",
            "notes": "Revision with corrected regular capacity",
            "allocations": [
                {"seatClassification": "APPROVED_REGULAR", "approvedCount": 45},
                {
                    "seatClassification": "APPROVED_SUPERNUMERARY",
                    "approvedCount": 4,
                    "authorizationReference": "AICTE/SN/2026-27/XYZ",
                },
            ],
        },
        headers=supervisor,
    )
    assert revised.status_code == 201, revised.text
    assert revised.json()["version"] == 2

    history = client.get(
        f"/api/v1/programmes/{programme_id}/intake-snapshots", headers=supervisor
    )
    assert history.status_code == 200
    statuses = {item["version"]: item["status"] for item in history.json()}
    assert statuses == {1: "SUPERSEDED", 2: "ACTIVE"}


def test_supernumerary_snapshot_requires_authorization_reference(client, seeded) -> None:
    headers = auth_headers(client, "supervisor@aicte.demo")
    response = client.post(
        "/api/v1/programmes/prog_ait_cse/intake-snapshots",
        json={
            "academicYear": "2027-28",
            "approvalReference": "AICTE/APPR/2027-28/AIT-CSE",
            "validFrom": "2027-06-01",
            "allocations": [
                {"seatClassification": "APPROVED_REGULAR", "approvedCount": 120},
                {"seatClassification": "APPROVED_SUPERNUMERARY", "approvedCount": 5},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_programme_list_is_forced_to_own_institution(client, seeded) -> None:
    headers = auth_headers(client, "operator@demo-ait.edu")
    response = client.get(
        "/api/v1/programmes?institutionId=inst_bie", headers=headers
    )
    assert response.status_code == 200
    assert response.json()
    assert all(item["institutionId"] == "inst_ait" for item in response.json())

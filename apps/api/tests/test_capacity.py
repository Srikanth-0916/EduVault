"""Capacity rules: regular and supernumerary allocations stay separate."""

from __future__ import annotations

from app.models.enums import CapacityStatus
from app.services.capacity import calculate_capacity
from sqlalchemy.orm import Session


def test_capacity_keeps_regular_and_supernumerary_separate(seeded: Session) -> None:
    result = calculate_capacity(seeded, "prog_ait_cse", "2026-27")
    assert result.allocations["APPROVED_REGULAR"] == 120
    assert result.allocations["APPROVED_SUPERNUMERARY"] == 12
    assert result.evidence["regularApproved"] == 120
    assert result.evidence["supernumeraryApproved"] == 12
    assert result.reported == 24
    assert result.status == CapacityStatus.WITHIN_APPROVED_PLUS_AUTHORIZED_SUPERNUMERARY.value


def test_over_intake_is_a_possible_excess_not_an_automatic_finding(
    seeded: Session,
) -> None:
    result = calculate_capacity(seeded, "prog_cim_bba", "2026-27")
    assert result.allocations["APPROVED_REGULAR"] == 3
    assert result.reported == 4
    assert result.status == CapacityStatus.POSSIBLE_EXCESS.value
    assert "regular" in result.evidence["reason"].lower()


def test_missing_approval_data_is_explicit(seeded: Session) -> None:
    result = calculate_capacity(seeded, "prog_ait_cse", "2024-25")
    assert result.status == CapacityStatus.MISSING_APPROVAL_DATA.value
    assert result.allocations["APPROVED_REGULAR"] == 0

"""External APAAR verification adapter boundary.

The prototype ships one deterministic mock provider. Real integration must
replace the adapter, not sprinkle network calls through the workflow layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from app.security import is_valid_apaar, normalize_apaar


@dataclass(frozen=True)
class ApaarVerificationResult:
    outcome: str
    reference: str
    checked_at: datetime
    adapter_version: str
    mock: bool = True
    detail: dict[str, Any] = field(default_factory=dict)


class ApaarVerificationProvider(Protocol):
    version: str

    def verify(
        self,
        identifier: str,
        purpose: str,
        consent_context: dict[str, Any] | None = None,
    ) -> ApaarVerificationResult: ...


class MockApaarProvider:
    """Deterministic sandbox adapter; never contacts a government system.

    Outcomes are intentionally stable for demos:

    - last two digits ``99`` → ``MISMATCH``
    - last two digits ``88`` → ``UNAVAILABLE``
    - otherwise valid 12 digits → ``SUCCESS``
    - invalid values → ``NOT_FOUND``
    """

    version = "mock-1.0"

    def verify(
        self,
        identifier: str,
        purpose: str,
        consent_context: dict[str, Any] | None = None,
    ) -> ApaarVerificationResult:
        normalized = normalize_apaar(identifier)
        now = datetime.now(UTC)
        if not is_valid_apaar(normalized):
            outcome = "NOT_FOUND"
        elif normalized is not None and normalized.endswith("99"):
            outcome = "MISMATCH"
        elif normalized is not None and normalized.endswith("88"):
            outcome = "UNAVAILABLE"
        else:
            outcome = "SUCCESS"

        reference = f"mock-apaar-{outcome.lower()}-{normalized[-4:] if normalized else 'none'}"
        return ApaarVerificationResult(
            outcome=outcome,
            reference=reference,
            checked_at=now,
            adapter_version=self.version,
            mock=True,
            detail={
                "purpose": purpose,
                "consentContext": bool(consent_context),
                "sandbox": True,
            },
        )


def get_apaar_provider() -> ApaarVerificationProvider:
    return MockApaarProvider()

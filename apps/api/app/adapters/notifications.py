"""Mock notification adapter.

The prototype has no mail provider. Email delivery is recorded as ``MOCKED``
so the UI never implies that a real message left the system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    status: str
    reference: str | None = None
    mock: bool = True


class MockNotificationAdapter:
    version = "mock-notify-1.0"

    def send_email(self, recipient: str, subject: str, body: str) -> DeliveryResult:
        return DeliveryResult(
            channel="EMAIL",
            status="MOCKED",
            reference=f"mock-email-{abs(hash((recipient, subject, body))) % 10_000_000:07d}",
            mock=True,
        )


def get_notification_adapter() -> MockNotificationAdapter:
    return MockNotificationAdapter()

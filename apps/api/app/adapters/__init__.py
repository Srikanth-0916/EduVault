"""External adapter package. All providers here are mock/sandbox in the prototype."""

from app.adapters.apaar import (
    ApaarVerificationProvider,
    ApaarVerificationResult,
    MockApaarProvider,
    get_apaar_provider,
)

__all__ = [
    "ApaarVerificationProvider",
    "ApaarVerificationResult",
    "MockApaarProvider",
    "get_apaar_provider",
]

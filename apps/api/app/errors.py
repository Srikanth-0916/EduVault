"""API error types and the canonical error payload shape.

Error responses always use::

    {"error": {"code": ..., "message": ..., "details": ...}, "traceId": ...}
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Application-level error carried to the client with a stable code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

    def payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


def not_found(message: str = "Resource not found", details: Any = None) -> AppError:
    """A generic 404 that does not confirm whether the resource ever existed."""
    return AppError(404, "NOT_FOUND", message, details)


def forbidden(
    message: str = "You do not have access to this resource", details: Any = None
) -> AppError:
    return AppError(403, "FORBIDDEN", message, details)


def conflict(message: str, details: Any = None) -> AppError:
    return AppError(409, "CONFLICT", message, details)


def validation_error(message: str = "Request payload is invalid", details: Any = None) -> AppError:
    return AppError(422, "VALIDATION_ERROR", message, details)


def internal_error() -> AppError:
    """A 500 that leaks nothing about the underlying failure."""
    return AppError(500, "INTERNAL_ERROR", "Unexpected server error")

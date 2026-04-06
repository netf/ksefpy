from __future__ import annotations

from typing import Any


class KSeFError(Exception):
    """Base exception for all KSeF SDK errors."""


class KSeFApiError(KSeFError):
    """API returned an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []


class KSeFUnauthorizedError(KSeFApiError):
    """HTTP 401 — authentication failed. Carries RFC 7807 ProblemDetails."""

    def __init__(self, message: str, problem: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=401)
        self.problem = problem or {}


class KSeFForbiddenError(KSeFApiError):
    """HTTP 403 — insufficient permissions. Carries RFC 7807 ProblemDetails."""

    def __init__(self, message: str, problem: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=403)
        self.problem = problem or {}


class KSeFRateLimitError(KSeFApiError):
    """HTTP 429 — rate limited."""

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        limit: int | None = None,
        remaining: int | None = None,
    ) -> None:
        super().__init__(message=message, status_code=429)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining


class KSeFServerError(KSeFApiError):
    """HTTP 5xx — server-side error."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message=message, status_code=status_code)


class KSeFCryptoError(KSeFError):
    """Encryption, signing, or key management failure."""


class KSeFXmlError(KSeFError):
    """XML serialization, deserialization, or validation failure."""

    def __init__(self, message: str, validation_errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.validation_errors = validation_errors or []


class KSeFSessionError(KSeFError):
    """Session lifecycle error (expired, already closed, etc.)."""


class KSeFTimeoutError(KSeFError):
    """Polling timeout (UPO retrieval, auth status, export)."""

"""KSeF SDK exception hierarchy.

Public exceptions (raised to users of KSeF/AsyncKSeF):
    KSeFError            — base
    KSeFAuthError        — auth failures (401, challenge, token issues)
    KSeFInvoiceError     — invoice validation (400/450 on send)
    KSeFPermissionError  — 403
    KSeFRateLimitError   — 429 with retry_after
    KSeFSessionError     — session lifecycle
    KSeFServerError      — 5xx
    KSeFTimeoutError     — polling timeouts

Internal exceptions (raised by low-level clients, caught and mapped in _client.py):
    _ApiError            — raw HTTP error from BaseClient
    KSeFCryptoError      — encryption/signing failures (stays internal)
    KSeFXmlError         — XML serialization/validation failures (stays internal)
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Public exception hierarchy
# ---------------------------------------------------------------------------


class KSeFError(Exception):
    """Base exception for all KSeF SDK errors."""

    def __init__(self, message: str, *, raw_response: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.raw_response: dict[str, Any] = raw_response or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.raw_response:
            return f"{base} (raw_response={self.raw_response!r})"
        return base


class KSeFAuthError(KSeFError):
    """Authentication failure (401, challenge failure, token issues)."""


class KSeFInvoiceError(KSeFError):
    """Invoice validation error (400/450 on send)."""


class KSeFPermissionError(KSeFError):
    """Permission denied (403)."""


class KSeFRateLimitError(KSeFError):
    """Rate limited (429)."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, raw_response=raw_response)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = Exception.__str__(self)
        parts = [base]
        if self.retry_after is not None:
            parts.append(f"retry_after={self.retry_after}")
        if self.raw_response:
            parts.append(f"raw_response={self.raw_response!r}")
        return " ".join(parts) if len(parts) > 1 else base


class KSeFSessionError(KSeFError):
    """Session lifecycle error (expired, already closed, etc.)."""


class KSeFServerError(KSeFError):
    """Server-side error (5xx)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, raw_response=raw_response)
        self.status_code = status_code


class KSeFTimeoutError(KSeFError):
    """Polling timeout (UPO retrieval, auth status, export)."""


# ---------------------------------------------------------------------------
# Internal exceptions (not part of the public API)
# ---------------------------------------------------------------------------


class _ApiError(Exception):
    """Internal exception raised by BaseClient._handle_response.

    Caught by _client.py and mapped to the appropriate public exception.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        raw_response: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.raw_response: dict[str, Any] = raw_response or {}
        self.retry_after = retry_after


class KSeFCryptoError(KSeFError):
    """Encryption, signing, or key management failure."""


class KSeFXmlError(KSeFError):
    """XML serialization, deserialization, or validation failure."""

    def __init__(
        self,
        message: str,
        *,
        validation_errors: list[str] | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, raw_response=raw_response)
        self.validation_errors = validation_errors or []



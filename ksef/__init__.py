"""KSeF Python SDK — high-level API.

The primary public interface is :class:`KSeF` (sync) and :class:`AsyncKSeF` (async).

Example::

    from ksef import KSeF

    with KSeF("1234567890", token="your-token", env="test") as ksef:
        result = ksef.send_invoice(xml_bytes)
        print(result.reference_number)
"""

from __future__ import annotations

from typing import Any

from ksef._client import AsyncKSeF
from ksef._sync import SyncWrapper
from ksef._types import InvoiceResult, LimitsInfo, SessionStatus, TokenResult
from ksef._version import __version__
from ksef.environments import Environment
from ksef.exceptions import (
    KSeFAuthError,
    KSeFError,
    KSeFInvoiceError,
    KSeFPermissionError,
    KSeFRateLimitError,
    KSeFServerError,
    KSeFSessionError,
    KSeFTimeoutError,
)


class KSeF:
    """Synchronous KSeF client. Wraps :class:`AsyncKSeF` on a private event loop."""

    def __init__(
        self,
        nip: str,
        *,
        token: str | None = None,
        cert: bytes | None = None,
        key: bytes | None = None,
        env: str | Environment = "production",
        timeout: float = 30.0,
    ) -> None:
        self._async = AsyncKSeF(
            nip, token=token, cert=cert, key=key, env=env, timeout=timeout,
        )
        self._wrapper = SyncWrapper(self._async)

    def __enter__(self) -> KSeF:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._wrapper.close()

    def session(self, schema: str = "FA(3)") -> None:  # noqa: ARG002
        """Not available in sync mode — use ``AsyncKSeF.session()`` instead."""
        raise NotImplementedError(
            "session() context manager requires async. Use AsyncKSeF instead, "
            "or use send_invoices() for batch sending in sync mode."
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapper, name)


__all__ = [
    "__version__",
    "AsyncKSeF",
    "Environment",
    "InvoiceResult",
    "KSeF",
    "KSeFAuthError",
    "KSeFError",
    "KSeFInvoiceError",
    "KSeFPermissionError",
    "KSeFRateLimitError",
    "KSeFServerError",
    "KSeFSessionError",
    "KSeFTimeoutError",
    "LimitsInfo",
    "SessionStatus",
    "TokenResult",
]

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ksef._sync import SyncWrapper
from ksef._version import __version__
from ksef.client import AsyncKSeFClient
from ksef.environments import Environment

if TYPE_CHECKING:
    from ksef._sync import SyncSubClient


class KSeFClient:
    """Synchronous KSeF API client. Wraps AsyncKSeFClient."""

    # Declared for pyright — actual values come from __getattr__ → SyncWrapper
    auth: SyncSubClient
    sessions: SyncSubClient
    online: SyncSubClient
    batch: SyncSubClient
    session_status: SyncSubClient
    invoices: SyncSubClient
    permissions: SyncSubClient
    certificates: SyncSubClient
    tokens: SyncSubClient
    limits: SyncSubClient
    peppol: SyncSubClient
    testdata: SyncSubClient

    def __init__(self, environment: Environment, timeout: float = 30.0) -> None:
        self._async_client = AsyncKSeFClient(environment=environment, timeout=timeout)
        self._wrapper = SyncWrapper(self._async_client)

    def __enter__(self) -> KSeFClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._wrapper.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapper, name)


__all__ = ["__version__", "AsyncKSeFClient", "Environment", "KSeFClient"]

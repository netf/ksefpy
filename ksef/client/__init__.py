"""Low-level KSeF API client modules."""

from __future__ import annotations

from ksef.client.auth import AuthClient
from ksef.client.base import BaseClient
from ksef.client.batch import BatchSessionClient
from ksef.client.certificates import CertificateClient
from ksef.client.invoices import InvoiceClient
from ksef.client.limits import LimitsClient
from ksef.client.online import OnlineSessionClient
from ksef.client.peppol import PeppolClient
from ksef.client.permissions import PermissionClient
from ksef.client.session_status import SessionStatusClient
from ksef.client.sessions import ActiveSessionsClient
from ksef.client.testdata import TestDataClient
from ksef.client.tokens import KSeFTokenClient
from ksef.environments import Environment


class AsyncKSeFClient:
    """Aggregated async KSeF API client."""

    def __init__(self, environment: Environment, timeout: float = 30.0) -> None:
        self._base = BaseClient(environment=environment, timeout=timeout)
        self.auth = AuthClient(self._base)
        self.sessions = ActiveSessionsClient(self._base)
        self.online = OnlineSessionClient(self._base)
        self.batch = BatchSessionClient(self._base)
        self.session_status = SessionStatusClient(self._base)
        self.invoices = InvoiceClient(self._base)
        self.permissions = PermissionClient(self._base)
        self.certificates = CertificateClient(self._base)
        self.tokens = KSeFTokenClient(self._base)
        self.limits = LimitsClient(self._base)
        self.peppol = PeppolClient(self._base)
        self.testdata = TestDataClient(self._base)

    @property
    def environment(self) -> Environment:
        return self._base.environment

    async def close(self) -> None:
        await self._base.close()

    async def __aenter__(self) -> AsyncKSeFClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

"""Invoice download workflow coordinator for KSeF."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from ksef.exceptions import KSeFTimeoutError

if TYPE_CHECKING:
    from ksef.client import AsyncKSeFClient
    from ksef.coordinators.auth import AuthSession


class AsyncInvoiceDownloadManager:
    """Handles querying, downloading, and exporting KSeF invoices."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        auth_session: AuthSession,
    ) -> None:
        self._client = client
        self._auth_session = auth_session

    async def download(self, ksef_number: str) -> bytes:
        """Download a single invoice by its KSeF reference number.

        Returns raw XML bytes.
        """
        access_token = await self._auth_session.get_access_token()
        return await self._client.invoices.download(ksef_number, access_token=access_token)

    async def query_metadata(self, query: dict[str, Any]) -> dict:
        """Query invoice metadata with the given filter dict."""
        access_token = await self._auth_session.get_access_token()
        return await self._client.invoices.query_metadata(query, access_token=access_token)

    async def export(self, request: dict[str, Any]) -> dict:
        """Request an invoice export and return the initial response."""
        access_token = await self._auth_session.get_access_token()
        return await self._client.invoices.export(request, access_token=access_token)

    async def get_export_status(self, reference_number: str) -> dict:
        """Poll the status of an ongoing export."""
        access_token = await self._auth_session.get_access_token()
        return await self._client.invoices.get_export_status(
            reference_number, access_token=access_token
        )

    async def export_and_wait(
        self,
        request: dict[str, Any],
        *,
        poll_interval: float = 2.0,
        poll_timeout: float = 300.0,
    ) -> dict:
        """Request an export and poll until it completes or times out.

        Returns the final export status response.
        """
        export_resp = await self.export(request)
        reference_number = export_resp.get("referenceNumber") or export_resp.get("reference_number")
        if not reference_number:
            raise ValueError("Export response did not contain a referenceNumber")

        deadline = time.monotonic() + poll_timeout
        while True:
            status = await self.get_export_status(reference_number)
            code = None
            status_block = status.get("status", {})
            if isinstance(status_block, dict):
                code = status_block.get("code")
            if code == 200:
                return status
            if time.monotonic() >= deadline:
                raise KSeFTimeoutError(
                    f"Export polling timed out after {poll_timeout}s "
                    f"(referenceNumber={reference_number})"
                )
            await asyncio.sleep(poll_interval)

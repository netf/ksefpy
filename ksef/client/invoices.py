from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient


class InvoiceClient:
    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def download(self, ksef_number: str, *, access_token: str) -> bytes:
        return await self._base.get_raw(f"invoices/ksef/{ksef_number}", access_token=access_token)

    async def query_metadata(self, query: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("invoices/query/metadata", access_token=access_token, json=query)

    async def export(self, request: dict[str, Any], *, access_token: str) -> dict:
        return await self._base.post("invoices/exports", access_token=access_token, json=request)

    async def get_export_status(self, reference_number: str, *, access_token: str) -> dict:
        return await self._base.get(f"invoices/exports/{reference_number}", access_token=access_token)

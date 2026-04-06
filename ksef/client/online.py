from __future__ import annotations

from ksef.client.base import BaseClient
from ksef.models.sessions import (
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
)


class OnlineSessionClient:
    """Client for KSeF interactive (online) session endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def open(
        self,
        request: OpenOnlineSessionRequest,
        *,
        access_token: str,
        upo_version: str | None = None,
    ) -> OpenOnlineSessionResponse:
        """POST /sessions/online"""
        headers: dict[str, str] = {}
        if upo_version:
            headers["X-KSeF-Feature"] = f"upo-version:{upo_version}"
        data = await self._base.post(
            "sessions/online",
            access_token=access_token,
            json=request.model_dump(by_alias=True, exclude_none=True),
            headers=headers or None,
        )
        return OpenOnlineSessionResponse.model_validate(data)

    async def send_invoice(
        self,
        request: SendInvoiceRequest,
        session_reference_number: str,
        *,
        access_token: str,
    ) -> SendInvoiceResponse:
        """POST /sessions/online/{ref}/invoices"""
        data = await self._base.post(
            f"sessions/online/{session_reference_number}/invoices",
            access_token=access_token,
            json=request.model_dump(by_alias=True, exclude_none=True),
        )
        return SendInvoiceResponse.model_validate(data)

    async def close(self, session_reference_number: str, *, access_token: str) -> None:
        """POST /sessions/online/{ref}/close"""
        await self._base.post(
            f"sessions/online/{session_reference_number}/close",
            access_token=access_token,
        )

from __future__ import annotations

from typing import Any

from ksef.client.base import BaseClient
from ksef.models.sessions import SessionStatusResponse


class SessionStatusClient:
    """Client for session status, invoice status, and UPO endpoints."""

    def __init__(self, base: BaseClient) -> None:
        self._base = base

    async def get_session_status(self, reference_number: str, *, access_token: str) -> SessionStatusResponse:
        """GET /sessions/{ref}"""
        data = await self._base.get(f"sessions/{reference_number}", access_token=access_token)
        return SessionStatusResponse.model_validate(data)

    async def get_session_invoices(
        self, reference_number: str, *, access_token: str, params: dict[str, Any] | None = None
    ) -> dict:
        """GET /sessions/{ref}/invoices"""
        return await self._base.get(f"sessions/{reference_number}/invoices", access_token=access_token, params=params)

    async def get_failed_invoices(
        self, reference_number: str, *, access_token: str, params: dict[str, Any] | None = None
    ) -> dict:
        """GET /sessions/{ref}/invoices/failed"""
        return await self._base.get(
            f"sessions/{reference_number}/invoices/failed", access_token=access_token, params=params
        )

    async def get_invoice_status(self, session_ref: str, invoice_ref: str, *, access_token: str) -> dict:
        """GET /sessions/{ref}/invoices/{invoiceRef}"""
        return await self._base.get(f"sessions/{session_ref}/invoices/{invoice_ref}", access_token=access_token)

    async def get_upo(self, session_ref: str, upo_ref: str, *, access_token: str) -> dict:
        """GET /sessions/{ref}/upo/{upoRef}"""
        return await self._base.get(f"sessions/{session_ref}/upo/{upo_ref}", access_token=access_token)

    async def get_upo_by_ksef_number(self, session_ref: str, ksef_number: str, *, access_token: str) -> dict:
        """GET /sessions/{ref}/invoices/ksef/{ksefNumber}/upo"""
        return await self._base.get(
            f"sessions/{session_ref}/invoices/ksef/{ksef_number}/upo", access_token=access_token
        )

    async def get_upo_by_invoice_reference(self, session_ref: str, invoice_ref: str, *, access_token: str) -> dict:
        """GET /sessions/{ref}/invoices/{invoiceRef}/upo"""
        return await self._base.get(f"sessions/{session_ref}/invoices/{invoice_ref}/upo", access_token=access_token)

    async def list_sessions(self, *, access_token: str, params: dict[str, Any] | None = None) -> dict:
        """GET /sessions — list/query sessions with filters."""
        return await self._base.get("sessions", access_token=access_token, params=params)

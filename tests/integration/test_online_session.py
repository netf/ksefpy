"""Integration tests for online (interactive) session endpoints."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.coordinators.online_session import AsyncOnlineSessionManager
from ksef.models.sessions import SessionStatusResponse
from ksef.testing import generate_test_invoice_xml

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def online_session_data(client: AsyncKSeFClient, auth_session: AuthSession, nip: str):
    """Open session, send invoice, close, yield references."""
    # Use the coordinator to get a warmed-up crypto service
    coordinator = AsyncAuthCoordinator(client)
    crypto = await coordinator._get_or_create_crypto()

    manager = AsyncOnlineSessionManager(client, auth_session, crypto=crypto)
    session_ref = None
    invoice_ref = None

    async with manager.open(schema_version="FA(3)") as ctx:
        session_ref = ctx.reference_number
        xml = generate_test_invoice_xml(nip)
        result = await ctx.send_invoice_xml(xml)
        invoice_ref = result.reference_number

    await asyncio.sleep(3)
    return {"session_ref": session_ref, "invoice_ref": invoice_ref}


async def test_open_online_session(online_session_data: dict):
    assert online_session_data["session_ref"]


async def test_send_invoice(online_session_data: dict):
    assert online_session_data["invoice_ref"]


async def test_close_online_session(online_session_data: dict):
    assert online_session_data["session_ref"]


async def test_get_session_status(client: AsyncKSeFClient, auth_session: AuthSession, online_session_data: dict):
    token = await auth_session.get_access_token()
    status = await client.session_status.get_session_status(
        online_session_data["session_ref"], access_token=token
    )
    assert isinstance(status, SessionStatusResponse)
    assert status.invoice_count is not None

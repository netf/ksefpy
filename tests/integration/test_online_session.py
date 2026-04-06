"""Integration tests for online (interactive) session endpoints."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from ksef import AsyncKSeF
from ksef.result import InvoiceResult, SessionStatus
from ksef.testing import generate_test_invoice_xml

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def session_data(client: AsyncKSeF, nip: str):
    """Open session, send invoice, close, yield references."""
    session_ref = None
    invoice_ref = None

    async with client.session() as s:
        session_ref = s.reference_number
        xml = generate_test_invoice_xml(nip)
        result = await s.send(xml)
        invoice_ref = result.reference_number

    await asyncio.sleep(3)
    return {"session_ref": session_ref, "invoice_ref": invoice_ref}


async def test_open_online_session(session_data: dict):
    assert session_data["session_ref"]


async def test_send_invoice(session_data: dict):
    assert session_data["invoice_ref"]


async def test_send_single_invoice(client: AsyncKSeF, nip: str):
    """send_invoice() opens and closes a session automatically."""
    xml = generate_test_invoice_xml(nip)
    result = await client.send_invoice(xml)
    assert isinstance(result, InvoiceResult)
    assert result.reference_number


async def test_session_context_collects_results(client: AsyncKSeF, nip: str):
    """The session context manager collects results from all sends."""
    xml1 = generate_test_invoice_xml(nip)
    xml2 = generate_test_invoice_xml(nip)
    async with client.session() as s:
        r1 = await s.send(xml1)
        r2 = await s.send(xml2)
    assert len(s.results) == 2
    assert r1.reference_number
    assert r2.reference_number


async def test_get_session_status(client: AsyncKSeF, session_data: dict):
    status = await client.get_session_status(session_data["session_ref"])
    assert isinstance(status, SessionStatus)
    assert status.invoice_count is not None

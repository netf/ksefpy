"""Integration tests for online (interactive) session endpoints."""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from ksef import AsyncKSeF, InvoiceResult, SessionStatus
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


async def test_download_sent_invoice(client: AsyncKSeF, nip: str):
    """Send a fresh invoice, poll for ksefNumber, then download the XML."""
    xml = generate_test_invoice_xml(nip)

    # Send in a session so we get the session reference
    async with client.session() as s:
        result = await s.send(xml)
        session_ref = s.reference_number
    invoice_ref = result.reference_number

    # Poll until ksefNumber is assigned — try both per-invoice and session-level
    await client._ensure_auth()
    ksef_number = None
    for _ in range(30):
        await asyncio.sleep(3)
        token = await client._get_access_token()

        # Try per-invoice status first
        try:
            inv = await client._client.session_status.get_invoice_status(
                session_ref,
                invoice_ref,
                access_token=token,
            )
            ksef_number = inv.get("ksefNumber")
        except Exception:
            pass

        # Fallback: check session invoices list
        if not ksef_number:
            try:
                resp = await client._client.session_status.get_session_invoices(
                    session_ref,
                    access_token=token,
                )
                for inv_item in resp.get("invoices", []):
                    if inv_item.get("referenceNumber") == invoice_ref:
                        ksef_number = inv_item.get("ksefNumber")
                        break
            except Exception:
                pass

        if ksef_number:
            break

    assert ksef_number, "ksefNumber not assigned within 90s"

    # Download with retry (server may need a moment after assigning the number)
    xml_bytes = None
    for _ in range(5):
        try:
            xml_bytes = await client.download_invoice(ksef_number)
            break
        except Exception:
            await asyncio.sleep(3)

    assert xml_bytes is not None, "download_invoice failed after 5 retries"
    assert len(xml_bytes) > 0
    assert b"Faktura" in xml_bytes


async def test_qr_url(client: AsyncKSeF):
    """qr_url() builds a valid KSeF QR verification URL."""
    from datetime import date

    url = client.qr_url(
        invoice_date=date(2026, 4, 6),
        seller_nip="1234567890",
        file_hash="abc123def456",
    )
    assert url.startswith("https://qr-test.ksef.mf.gov.pl/")
    assert "06-04-2026" in url
    assert "1234567890" in url
    assert "abc123def456" in url

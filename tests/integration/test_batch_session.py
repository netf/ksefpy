"""Integration tests for batch session (send_invoices)."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF
from ksef.result import InvoiceResult
from ksef.testing import generate_test_invoice_xml

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_send_invoices_batch(client: AsyncKSeF, nip: str):
    """send_invoices() sends multiple invoices in a single session."""
    xmls = [generate_test_invoice_xml(nip) for _ in range(3)]
    results = await client.send_invoices(xmls)
    assert len(results) == 3
    for r in results:
        assert isinstance(r, InvoiceResult)
        assert r.reference_number

"""Integration tests for invoice query and download endpoints."""

from __future__ import annotations

import datetime

import pytest

from ksef import AsyncKSeF
from ksef.exceptions import KSeFError

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_query_invoices(client: AsyncKSeF):
    today = datetime.date.today()
    month_ago = today - datetime.timedelta(days=30)
    resp = await client.query_invoices(
        subjectType="subject1",
        dateRange={
            "dateType": "invoicing",
            "from": month_ago.isoformat() + "T00:00:00",
            "to": today.isoformat() + "T23:59:59",
        },
    )
    assert isinstance(resp, dict)
    assert "invoices" in resp


async def test_download_invoice_not_found(client: AsyncKSeF):
    with pytest.raises(KSeFError):
        await client.download_invoice("0000000000-20260101-000000-0000000000")


async def test_export_invoices(client: AsyncKSeF):
    """export_invoices() requests an export and returns a reference number."""
    today = datetime.date.today()
    resp = await client.export_invoices(
        subjectType="subject1",
        dateRange={
            "dateType": "invoicing",
            "from": f"{today}T00:00:00",
            "to": f"{today}T23:59:59",
        },
    )
    assert isinstance(resp, dict)
    assert "referenceNumber" in resp

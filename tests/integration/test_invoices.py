"""Integration tests for invoice query and download endpoints."""
from __future__ import annotations

import datetime

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_query_metadata(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    today = datetime.date.today()
    month_ago = today - datetime.timedelta(days=30)
    resp = await client.invoices.query_metadata(
        {
            "subjectType": "subject1",
            "dateRange": {
                "dateType": "invoicing",
                "from": month_ago.isoformat() + "T00:00:00",
                "to": today.isoformat() + "T23:59:59",
            },
        },
        access_token=token,
    )
    assert isinstance(resp, dict)
    assert "invoices" in resp


async def test_download_invoice_not_found(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    with pytest.raises(Exception):
        await client.invoices.download("0000000000-20260101-000000-0000000000", access_token=token)

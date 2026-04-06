import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.session_status import SessionStatusClient
from ksef.environments import Environment
from ksef.models.sessions import SessionStatusResponse

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def status_client():
    return SessionStatusClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_get_session_status(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1").mock(
        return_value=httpx.Response(200, json={
            "status": {"code": "200", "description": "OK"},
            "invoiceCount": 3,
            "successfulInvoiceCount": 2,
            "failedInvoiceCount": 1,
            "dateCreated": "2026-04-06T10:00:00+00:00",
            "dateUpdated": "2026-04-06T10:05:00+00:00",
        })
    )
    result = await status_client.get_session_status("sess-1", access_token="tok")
    assert isinstance(result, SessionStatusResponse)
    assert result.invoice_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_get_session_invoices(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1/invoices").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    result = await status_client.get_session_invoices("sess-1", access_token="tok")
    assert result == {"items": []}


@respx.mock
@pytest.mark.asyncio
async def test_get_upo(status_client: SessionStatusClient):
    respx.get(f"{BASE}/sessions/sess-1/upo/upo-ref").mock(
        return_value=httpx.Response(200, json={"upo": "data"})
    )
    result = await status_client.get_upo("sess-1", "upo-ref", access_token="tok")
    assert result == {"upo": "data"}

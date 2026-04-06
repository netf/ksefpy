import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.invoices import InvoiceClient
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def invoice_client():
    return InvoiceClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_download_invoice(invoice_client: InvoiceClient):
    respx.get(f"{BASE}/invoices/ksef/KSEF-123").mock(
        return_value=httpx.Response(200, content=b"<xml>invoice</xml>", headers={"Content-Type": "application/xml"})
    )
    result = await invoice_client.download("KSEF-123", access_token="tok")
    assert result == b"<xml>invoice</xml>"


@respx.mock
@pytest.mark.asyncio
async def test_query_metadata(invoice_client: InvoiceClient):
    respx.post(f"{BASE}/invoices/query/metadata").mock(
        return_value=httpx.Response(200, json={"items": [], "continuationToken": None})
    )
    result = await invoice_client.query_metadata(
        {"dateFrom": "2026-01-01", "dateTo": "2026-03-31"},
        access_token="tok",
    )
    assert result["items"] == []


@respx.mock
@pytest.mark.asyncio
async def test_export(invoice_client: InvoiceClient):
    respx.post(f"{BASE}/invoices/exports").mock(
        return_value=httpx.Response(200, json={"referenceNumber": "exp-1"})
    )
    result = await invoice_client.export(
        {"dateFrom": "2026-01-01", "dateTo": "2026-03-31"},
        access_token="tok",
    )
    assert result["referenceNumber"] == "exp-1"


@respx.mock
@pytest.mark.asyncio
async def test_get_export_status(invoice_client: InvoiceClient):
    respx.get(f"{BASE}/invoices/exports/exp-1").mock(
        return_value=httpx.Response(200, json={"status": {"code": "200"}})
    )
    result = await invoice_client.get_export_status("exp-1", access_token="tok")
    assert result["status"]["code"] == "200"

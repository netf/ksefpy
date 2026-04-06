import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.coordinators.invoice_download import AsyncInvoiceDownloadManager
from ksef.environments import Environment
from ksef.models.auth import TokenInfo

BASE = "https://api-test.ksef.mf.gov.pl/v2"


def _make_session(client):
    return AuthSession(
        client=client,
        access_token=TokenInfo(token="access-jwt", valid_until="2099-01-01T00:00:00+00:00"),
        refresh_token=TokenInfo(token="refresh-jwt", valid_until="2099-01-07T00:00:00+00:00"),
    )


@respx.mock
@pytest.mark.asyncio
async def test_download_invoice():
    respx.get(f"{BASE}/invoices/ksef/KSEF-NUM-1").mock(
        return_value=httpx.Response(200, content=b"<Faktura/>", headers={"Content-Type": "application/xml"})
    )

    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        session = _make_session(client)
        downloader = AsyncInvoiceDownloadManager(client, session)
        xml = await downloader.download("KSEF-NUM-1")
        assert xml == b"<Faktura/>"

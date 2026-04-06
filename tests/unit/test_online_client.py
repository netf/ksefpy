import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.online import OnlineSessionClient
from ksef.environments import Environment
from ksef.models.sessions import (
    EncryptionInfo,
    FormCode,
    OpenOnlineSessionRequest,
    OpenOnlineSessionResponse,
    SendInvoiceRequest,
    SendInvoiceResponse,
)

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def online_client():
    return OnlineSessionClient(BaseClient(environment=Environment.TEST))


@respx.mock
@pytest.mark.asyncio
async def test_open_online_session(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online").mock(
        return_value=httpx.Response(201, json={
            "referenceNumber": "sess-1",
            "validUntil": "2026-04-06T22:00:00+00:00",
        })
    )
    req = OpenOnlineSessionRequest(
        form_code=FormCode(system_code="FA (3)", schema_version="1-0E", value="FA"),
        encryption=EncryptionInfo(encrypted_symmetric_key="key", initialization_vector="iv"),
    )
    result = await online_client.open(req, access_token="tok")
    assert isinstance(result, OpenOnlineSessionResponse)
    assert result.reference_number == "sess-1"


@respx.mock
@pytest.mark.asyncio
async def test_send_invoice(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online/sess-1/invoices").mock(
        return_value=httpx.Response(202, json={"referenceNumber": "inv-1"})
    )
    req = SendInvoiceRequest(
        invoice_hash="hash1", invoice_size=100,
        encrypted_invoice_hash="enchash1", encrypted_invoice_size=120,
        encrypted_invoice_content="base64data",
    )
    result = await online_client.send_invoice(req, "sess-1", access_token="tok")
    assert isinstance(result, SendInvoiceResponse)
    assert result.reference_number == "inv-1"


@respx.mock
@pytest.mark.asyncio
async def test_close_session(online_client: OnlineSessionClient):
    respx.post(f"{BASE}/sessions/online/sess-1/close").mock(
        return_value=httpx.Response(200, json={})
    )
    await online_client.close("sess-1", access_token="tok")

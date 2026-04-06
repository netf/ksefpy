import httpx
import pytest
import respx

from ksef.client.base import BaseClient
from ksef.client.batch import BatchSessionClient
from ksef.client.certificates import CertificateClient
from ksef.client.limits import LimitsClient
from ksef.client.peppol import PeppolClient
from ksef.client.permissions import PermissionClient
from ksef.client.sessions import ActiveSessionsClient
from ksef.client.testdata import TestDataClient
from ksef.client.tokens import KSeFTokenClient
from ksef.environments import Environment

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def base():
    return BaseClient(environment=Environment.TEST)


@respx.mock
@pytest.mark.asyncio
async def test_active_sessions_list(base: BaseClient):
    respx.get(f"{BASE}/auth/sessions").mock(return_value=httpx.Response(200, json={"items": []}))
    client = ActiveSessionsClient(base)
    result = await client.list_sessions(access_token="tok")
    assert result == {"items": []}


@respx.mock
@pytest.mark.asyncio
async def test_batch_open(base: BaseClient):
    respx.post(f"{BASE}/sessions/batch").mock(return_value=httpx.Response(201, json={"referenceNumber": "b-1"}))
    client = BatchSessionClient(base)
    result = await client.open({"formCode": {}}, access_token="tok")
    assert result["referenceNumber"] == "b-1"


@respx.mock
@pytest.mark.asyncio
async def test_tokens_generate(base: BaseClient):
    respx.post(f"{BASE}/tokens").mock(
        return_value=httpx.Response(202, json={"referenceNumber": "t-1", "token": "generated-tok"})
    )
    client = KSeFTokenClient(base)
    result = await client.generate({"permissions": ["InvoiceWrite"]}, access_token="tok")
    assert result["referenceNumber"] == "t-1"


@respx.mock
@pytest.mark.asyncio
async def test_tokens_revoke(base: BaseClient):
    respx.delete(f"{BASE}/tokens/t-1").mock(return_value=httpx.Response(204))
    client = KSeFTokenClient(base)
    await client.revoke("t-1", access_token="tok")


@respx.mock
@pytest.mark.asyncio
async def test_limits_context(base: BaseClient):
    respx.get(f"{BASE}/limits/context").mock(return_value=httpx.Response(200, json={"maxOnlineSessions": 5}))
    client = LimitsClient(base)
    result = await client.get_context_limits(access_token="tok")
    assert result["maxOnlineSessions"] == 5


@respx.mock
@pytest.mark.asyncio
async def test_permissions_grant_person(base: BaseClient):
    respx.post(f"{BASE}/permissions/persons/grants").mock(
        return_value=httpx.Response(200, json={"referenceNumber": "p-1"})
    )
    client = PermissionClient(base)
    result = await client.grant_person({}, access_token="tok")
    assert result["referenceNumber"] == "p-1"


@respx.mock
@pytest.mark.asyncio
async def test_certificates_get_limits(base: BaseClient):
    respx.get(f"{BASE}/certificates/limits").mock(
        return_value=httpx.Response(200, json={"limit": 6, "activeCount": 2})
    )
    client = CertificateClient(base)
    result = await client.get_limits(access_token="tok")
    assert result["limit"] == 6


@respx.mock
@pytest.mark.asyncio
async def test_peppol_query(base: BaseClient):
    respx.get(f"{BASE}/peppol/query").mock(
        return_value=httpx.Response(200, json={"peppolProviders": [], "hasMore": False})
    )
    client = PeppolClient(base)
    result = await client.query(access_token="tok", params={"pageSize": 10})
    assert result["peppolProviders"] == []


@respx.mock
@pytest.mark.asyncio
async def test_testdata_create_subject(base: BaseClient):
    respx.post(f"{BASE}/testdata/subject").mock(return_value=httpx.Response(200, json={"ok": True}))
    client = TestDataClient(base)
    result = await client.create_subject({"nip": "1234567890"}, access_token="tok")
    assert result["ok"] is True

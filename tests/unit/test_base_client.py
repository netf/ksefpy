import httpx
import pytest
import respx

from ksef.client import AsyncKSeFClient
from ksef.client.base import BaseClient
from ksef.environments import Environment
from ksef.exceptions import _ApiError


@pytest.fixture
def base_client():
    client = BaseClient(environment=Environment.TEST)
    yield client


@respx.mock
@pytest.mark.asyncio
async def test_get_request(base_client: BaseClient):
    route = respx.get("https://api-test.ksef.mf.gov.pl/v2/auth/sessions").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    resp = await base_client.get("auth/sessions", access_token="tok")
    assert resp == {"items": []}
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_post_request(base_client: BaseClient):
    respx.post("https://api-test.ksef.mf.gov.pl/v2/auth/challenge").mock(
        return_value=httpx.Response(200, json={"challenge": "xyz"})
    )
    resp = await base_client.post("auth/challenge")
    assert resp == {"challenge": "xyz"}


@respx.mock
@pytest.mark.asyncio
async def test_auth_header_included(base_client: BaseClient):
    route = respx.get("https://api-test.ksef.mf.gov.pl/v2/some/path").mock(
        return_value=httpx.Response(200, json={})
    )
    await base_client.get("some/path", access_token="my-jwt")
    assert route.calls[0].request.headers["Authorization"] == "Bearer my-jwt"


@respx.mock
@pytest.mark.asyncio
async def test_400_raises_api_error(base_client: BaseClient):
    respx.post("https://api-test.ksef.mf.gov.pl/v2/bad").mock(
        return_value=httpx.Response(
            400,
            json={"exception": {"serviceCode": "20001", "exceptionDetailList": []}},
        )
    )
    with pytest.raises(_ApiError) as exc_info:
        await base_client.post("bad")
    assert exc_info.value.status_code == 400


@respx.mock
@pytest.mark.asyncio
async def test_401_raises_api_error(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/auth").mock(
        return_value=httpx.Response(401, json={"type": "about:blank", "title": "Unauthorized"})
    )
    with pytest.raises(_ApiError) as exc_info:
        await base_client.get("auth")
    assert exc_info.value.status_code == 401


@respx.mock
@pytest.mark.asyncio
async def test_403_raises_api_error(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/perm").mock(
        return_value=httpx.Response(403, json={"type": "about:blank", "title": "Forbidden"})
    )
    with pytest.raises(_ApiError) as exc_info:
        await base_client.get("perm")
    assert exc_info.value.status_code == 403


@respx.mock
@pytest.mark.asyncio
async def test_429_raises_api_error_with_retry_after(base_client: BaseClient):
    respx.post("https://api-test.ksef.mf.gov.pl/v2/invoke").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "30"}, json={})
    )
    with pytest.raises(_ApiError) as exc_info:
        await base_client.post("invoke")
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 30.0


@respx.mock
@pytest.mark.asyncio
async def test_500_raises_api_error(base_client: BaseClient):
    respx.get("https://api-test.ksef.mf.gov.pl/v2/down").mock(
        return_value=httpx.Response(502, text="Bad Gateway")
    )
    with pytest.raises(_ApiError) as exc_info:
        await base_client.get("down")
    assert exc_info.value.status_code == 502


@respx.mock
@pytest.mark.asyncio
async def test_delete_request(base_client: BaseClient):
    route = respx.delete("https://api-test.ksef.mf.gov.pl/v2/tokens/ref-1").mock(
        return_value=httpx.Response(204)
    )
    resp = await base_client.delete("tokens/ref-1", access_token="tok")
    assert resp is None
    assert route.called


@pytest.mark.asyncio
async def test_aggregated_client_has_all_sub_clients():
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        assert hasattr(client, "auth")
        assert hasattr(client, "sessions")
        assert hasattr(client, "online")
        assert hasattr(client, "batch")
        assert hasattr(client, "session_status")
        assert hasattr(client, "invoices")
        assert hasattr(client, "permissions")
        assert hasattr(client, "certificates")
        assert hasattr(client, "tokens")
        assert hasattr(client, "limits")
        assert hasattr(client, "peppol")
        assert hasattr(client, "testdata")

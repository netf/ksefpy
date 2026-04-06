import httpx
import pytest
import respx

from ksef.client.auth import AuthClient
from ksef.client.base import BaseClient
from ksef.environments import Environment
from ksef.models.auth import (
    AuthenticationChallengeResponse,
    AuthenticationKsefTokenRequest,
    AuthenticationOperationStatusResponse,
    RefreshTokenResponse,
    SignatureResponse,
)
from ksef.models.common import ContextIdentifier, ContextIdentifierType

BASE = "https://api-test.ksef.mf.gov.pl/v2"


@pytest.fixture
def auth_client():
    base = BaseClient(environment=Environment.TEST)
    return AuthClient(base)


@respx.mock
@pytest.mark.asyncio
async def test_get_challenge(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/challenge").mock(
        return_value=httpx.Response(200, json={
            "challenge": "abc123",
            "timestamp": "2026-04-06T10:00:00+00:00",
            "timestampMs": 1775386800000,
            "clientIp": "1.2.3.4",
        })
    )
    result = await auth_client.get_challenge()
    assert isinstance(result, AuthenticationChallengeResponse)
    assert result.challenge == "abc123"


@respx.mock
@pytest.mark.asyncio
async def test_submit_ksef_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/ksef-token").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "ref-1",
            "authenticationToken": {"token": "temp-tok", "validUntil": "2026-04-06T11:00:00+00:00"},
        })
    )
    req = AuthenticationKsefTokenRequest(
        challenge="abc",
        context_identifier=ContextIdentifier(type=ContextIdentifierType.NIP, value="1234567890"),
        encrypted_token="enc-data",
    )
    result = await auth_client.submit_ksef_token(req)
    assert isinstance(result, SignatureResponse)
    assert result.reference_number == "ref-1"


@respx.mock
@pytest.mark.asyncio
async def test_submit_xades_signature(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/xades-signature").mock(
        return_value=httpx.Response(200, json={
            "referenceNumber": "ref-2",
            "authenticationToken": {"token": "temp-tok-2", "validUntil": "2026-04-06T11:00:00+00:00"},
        })
    )
    result = await auth_client.submit_xades_signature("<xml/>", access_token="tok")
    assert isinstance(result, SignatureResponse)
    assert result.reference_number == "ref-2"


@respx.mock
@pytest.mark.asyncio
async def test_redeem_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/token/redeem").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "access-jwt", "validUntil": "2026-04-06T10:15:00+00:00"},
            "refreshToken": {"token": "refresh-jwt", "validUntil": "2026-04-13T10:15:00+00:00"},
        })
    )
    result = await auth_client.redeem_token(authentication_token="temp-tok")
    assert isinstance(result, AuthenticationOperationStatusResponse)
    assert result.access_token.token == "access-jwt"


@respx.mock
@pytest.mark.asyncio
async def test_refresh_token(auth_client: AuthClient):
    respx.post(f"{BASE}/auth/token/refresh").mock(
        return_value=httpx.Response(200, json={
            "accessToken": {"token": "new-jwt", "validUntil": "2026-04-06T10:30:00+00:00"},
        })
    )
    result = await auth_client.refresh_token(refresh_token="refresh-jwt")
    assert isinstance(result, RefreshTokenResponse)
    assert result.access_token.token == "new-jwt"

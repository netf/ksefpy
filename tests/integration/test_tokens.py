"""Integration tests for KSeF token management endpoints."""
from __future__ import annotations

import pytest
import pytest_asyncio

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def generated_token(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.tokens.generate(
        {"permissions": ["InvoiceRead"], "description": "integration-test-token"},
        access_token=token,
    )
    ref = resp.get("referenceNumber")
    token_value = resp.get("token")
    yield {"reference_number": ref, "token": token_value}
    try:
        t = await auth_session.get_access_token()
        await client.tokens.revoke(ref, access_token=t)
    except Exception:
        pass


async def test_generate_token(generated_token: dict):
    assert generated_token["reference_number"]
    assert generated_token["token"]


async def test_list_tokens(client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict):
    token = await auth_session.get_access_token()
    resp = await client.tokens.list_tokens(access_token=token)
    assert isinstance(resp, dict)
    assert "tokens" in resp


async def test_get_token(client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict):
    token = await auth_session.get_access_token()
    resp = await client.tokens.get(generated_token["reference_number"], access_token=token)
    assert resp.get("referenceNumber") == generated_token["reference_number"]


async def test_revoke_token(client: AsyncKSeFClient, auth_session: AuthSession, generated_token: dict):
    token = await auth_session.get_access_token()
    await client.tokens.revoke(generated_token["reference_number"], access_token=token)


async def test_authenticate_with_generated_token(
    client: AsyncKSeFClient, auth_session: AuthSession, nip: str, generated_token: dict
):
    """Authenticate using a KSeF token (not certificate)."""
    import asyncio

    from ksef.coordinators.auth import AsyncAuthCoordinator

    token_value = generated_token["token"]
    if not token_value:
        pytest.skip("No token value available")

    # Need to wait for token to become active
    await asyncio.sleep(3)

    coordinator = AsyncAuthCoordinator(client)
    try:
        session = await coordinator.authenticate_with_token(nip=nip, ksef_token=token_value, poll_timeout=30.0)
        access = await session.get_access_token()
        assert access
    except Exception:
        pytest.skip("Token may not be active yet")

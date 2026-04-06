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
    client: AsyncKSeFClient, auth_session: AuthSession, nip: str
):
    """Generate a fresh token and authenticate with it."""
    import asyncio

    from ksef.coordinators.auth import AsyncAuthCoordinator

    # Generate a dedicated token for this test (separate from the fixture's token)
    access_tok = await auth_session.get_access_token()
    resp = await client.tokens.generate(
        {"permissions": ["InvoiceRead", "InvoiceWrite"], "description": "auth-flow-test-token"},
        access_token=access_tok,
    )
    token_ref = resp.get("referenceNumber")
    token_value = resp.get("token")
    assert token_value, "Token generation did not return a token value"

    try:
        # Poll until token becomes Active
        for _ in range(30):
            access_tok = await auth_session.get_access_token()
            status_resp = await client.tokens.get(token_ref, access_token=access_tok)
            token_status = status_resp.get("status", {})
            code = token_status.get("code") if isinstance(token_status, dict) else token_status
            if str(code) == "200":
                break
            await asyncio.sleep(3)

        coordinator = AsyncAuthCoordinator(client)
        session = await coordinator.authenticate_with_token(nip=nip, ksef_token=token_value, poll_timeout=90.0)
        access = await session.get_access_token()
        assert access
        assert access != token_value
    finally:
        # Clean up: revoke the test token
        try:
            access_tok = await auth_session.get_access_token()
            await client.tokens.revoke(token_ref, access_token=access_tok)
        except Exception:
            pass

"""Integration tests for KSeF token management endpoints."""

from __future__ import annotations

import pytest
import pytest_asyncio

from ksef import AsyncKSeF
from ksef.result import TokenResult

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def generated_token(client: AsyncKSeF):
    result = await client.create_token(
        permissions=["InvoiceRead"],
        description="integration-test-token",
    )
    yield result
    try:
        await client.revoke_token(result.reference_number)
    except Exception:
        pass


async def test_create_token(generated_token: TokenResult):
    assert generated_token.reference_number
    assert generated_token.token


async def test_list_tokens(client: AsyncKSeF, generated_token: TokenResult):
    resp = await client.list_tokens()
    assert isinstance(resp, dict)
    assert "tokens" in resp


async def test_revoke_token(client: AsyncKSeF):
    """Create a token and immediately revoke it."""
    result = await client.create_token(
        permissions=["InvoiceRead"],
        description="revoke-test-token",
    )
    await client.revoke_token(result.reference_number)

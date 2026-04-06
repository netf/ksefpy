"""Integration tests for certificate endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_get_certificate_limits(client: AsyncKSeF):
    resp = await client.get_certificate_limits()
    assert isinstance(resp, dict)
    assert "canRequest" in resp


async def test_get_enrollment_data(client: AsyncKSeF):
    resp = await client.get_enrollment_data()
    assert isinstance(resp, dict)
    assert "commonName" in resp

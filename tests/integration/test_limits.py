"""Integration tests for limits endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF, LimitsInfo

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_get_limits(client: AsyncKSeF):
    limits = await client.get_limits()
    assert isinstance(limits, LimitsInfo)
    assert isinstance(limits.context, dict)
    assert isinstance(limits.subject, dict)
    assert isinstance(limits.rate, dict)

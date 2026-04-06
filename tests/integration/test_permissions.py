"""Integration tests for permission endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_query_permissions(client: AsyncKSeF):
    """POST /permissions/query/personal/grants -- query own permissions."""
    resp = await client.query_permissions()
    assert isinstance(resp, dict)


async def test_get_attachment_status(client: AsyncKSeF):
    resp = await client.get_attachment_status()
    assert isinstance(resp, dict)

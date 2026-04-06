"""Integration tests for session listing endpoints.

These endpoints are not exposed in the simplified API, so we access
the internal low-level client directly.
"""

from __future__ import annotations

import pytest

from ksef import AsyncKSeF

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_list_sessions(client: AsyncKSeF):
    await client._ensure_auth()
    access_token = await client._get_access_token()
    resp = await client._client.session_status.list_sessions(
        access_token=access_token, params={"pageSize": "10", "sessionType": "online"}
    )
    assert isinstance(resp, dict)


async def test_list_active_auth_sessions(client: AsyncKSeF):
    await client._ensure_auth()
    access_token = await client._get_access_token()
    resp = await client._client.sessions.list_sessions(access_token=access_token)
    assert isinstance(resp, dict)
    assert "items" in resp

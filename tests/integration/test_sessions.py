"""Integration tests for session listing endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_list_sessions(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.session_status.list_sessions(
        access_token=token, params={"pageSize": "10", "sessionType": "online"}
    )
    assert isinstance(resp, dict)


async def test_list_active_auth_sessions(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.sessions.list_sessions(access_token=token)
    assert isinstance(resp, dict)

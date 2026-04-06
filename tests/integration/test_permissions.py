"""Integration tests for permission endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_query_personal_permissions(client: AsyncKSeFClient, auth_session: AuthSession):
    """POST /permissions/query/personal/grants — query own permissions."""
    token = await auth_session.get_access_token()
    resp = await client.permissions.query_personal({}, access_token=token)
    assert isinstance(resp, dict)


async def test_get_attachment_status(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.permissions.get_attachment_status(access_token=token)
    assert isinstance(resp, dict)

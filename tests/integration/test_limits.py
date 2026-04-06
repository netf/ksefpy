"""Integration tests for limits and rate-limits endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = pytest.mark.integration


async def test_get_context_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    result = await client.limits.get_context_limits(access_token=token)
    assert isinstance(result, dict)


async def test_get_subject_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    result = await client.limits.get_subject_limits(access_token=token)
    assert isinstance(result, dict)


async def test_get_rate_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    result = await client.limits.get_rate_limits(access_token=token)
    assert isinstance(result, dict)

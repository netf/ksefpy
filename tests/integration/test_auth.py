"""Integration tests for authentication endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = pytest.mark.integration


async def test_get_challenge(client: AsyncKSeFClient):
    resp = await client.auth.get_challenge()
    assert resp.challenge
    assert resp.timestamp_ms > 0
    assert resp.client_ip


async def test_authenticate_produces_tokens(auth_session: AuthSession):
    assert auth_session.access_token_info.token
    assert auth_session.refresh_token_info.token


async def test_refresh_token(client: AsyncKSeFClient, auth_session: AuthSession):
    resp = await client.auth.refresh_token(refresh_token=auth_session.refresh_token_info.token)
    assert resp.access_token.token
    assert resp.access_token.valid_until

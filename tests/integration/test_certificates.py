"""Integration tests for certificate endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = pytest.mark.integration


async def test_get_certificate_limits(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_limits(access_token=token)
    assert isinstance(resp, dict)
    assert "canRequest" in resp


async def test_get_enrollment_data(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.certificates.get_enrollment_data(access_token=token)
    assert isinstance(resp, dict)
    assert "commonName" in resp

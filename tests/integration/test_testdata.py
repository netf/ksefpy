"""Integration tests for test data management endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession
from ksef.testing import generate_random_nip

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_create_and_remove_subject(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()
    await client.testdata.create_subject(
        {"subjectNip": test_nip, "description": "Integration Test Subject"},
        access_token=token,
    )
    # API returns 200 with empty body on success
    await client.testdata.remove_subject({"subjectNip": test_nip}, access_token=token)


async def test_create_and_remove_person(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    test_nip = generate_random_nip()
    resp = await client.testdata.create_person(
        {"personNip": test_nip, "firstName": "Test", "lastName": "Person", "isBailiff": False},
        access_token=token,
    )
    assert isinstance(resp, dict)
    resp = await client.testdata.remove_person({"personNip": test_nip}, access_token=token)
    assert isinstance(resp, dict)

"""Integration tests for permission endpoints."""
from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AuthSession

pytestmark = pytest.mark.integration


async def test_grant_and_query_person_permission(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    grant_resp = await client.permissions.grant_person(
        {
            "subjectIdentifier": {"type": "pesel", "value": "30112206276"},
            "permissions": ["InvoiceRead"],
            "description": "integration-test-grant",
            "subjectDetails": {
                "subjectDetailsType": "PersonById",
                "personById": {"firstName": "Test", "lastName": "User", "pesel": "30112206276"},
            },
        },
        access_token=token,
    )
    assert "referenceNumber" in grant_resp


async def test_get_attachment_status(client: AsyncKSeFClient, auth_session: AuthSession):
    token = await auth_session.get_access_token()
    resp = await client.permissions.get_attachment_status(access_token=token)
    assert isinstance(resp, dict)

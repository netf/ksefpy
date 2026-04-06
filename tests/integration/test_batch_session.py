"""Integration tests for batch session endpoints."""

from __future__ import annotations

import pytest

from ksef import AsyncKSeFClient
from ksef.coordinators.auth import AsyncAuthCoordinator, AuthSession
from ksef.models.sessions import EncryptionInfo, FormCode

pytestmark = [pytest.mark.integration, pytest.mark.asyncio(loop_scope="session")]


async def test_batch_open(client: AsyncKSeFClient, auth_session: AuthSession):
    coordinator = AsyncAuthCoordinator(client)
    crypto = await coordinator._get_or_create_crypto()

    materials = crypto.generate_session_materials()
    encryption = EncryptionInfo.from_session_materials(materials)
    token = await auth_session.get_access_token()

    resp = await client.batch.open(
        {
            "formCode": FormCode(
                system_code="FA (3)", schema_version="FA_2025010901", value="FA"
            ).model_dump(by_alias=True),
            "encryption": encryption.model_dump(by_alias=True),
            "batchFile": {
                "fileSize": 100,
                "fileHash": "a" * 64,
                "fileParts": [{"ordinalNumber": 1, "partName": "part_0001", "partSize": 100, "partHash": "a" * 64}],
            },
        },
        access_token=token,
    )
    assert "referenceNumber" in resp

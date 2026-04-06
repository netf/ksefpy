"""Integration tests for batch session endpoints."""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile

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

    # Build a tiny zip, encrypt it, compute proper hashes
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("invoice_0001.xml", "<Faktura/>")
    zip_bytes = buf.getvalue()
    encrypted = crypto.encrypt_aes256(zip_bytes, materials.key, materials.iv)

    file_hash = base64.b64encode(hashlib.sha256(zip_bytes).digest()).decode()
    part_hash = base64.b64encode(hashlib.sha256(encrypted).digest()).decode()

    token = await auth_session.get_access_token()

    resp = await client.batch.open(
        {
            "formCode": FormCode(
                system_code="FA (3)", schema_version="1-0E", value="FA"
            ).model_dump(by_alias=True),
            "encryption": encryption.model_dump(by_alias=True),
            "batchFile": {
                "fileSize": len(zip_bytes),
                "fileHash": file_hash,
                "fileParts": [
                    {
                        "ordinalNumber": 1,
                        "fileSize": len(encrypted),
                        "fileHash": part_hash,
                    }
                ],
            },
        },
        access_token=token,
    )
    assert "referenceNumber" in resp

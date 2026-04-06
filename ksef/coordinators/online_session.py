"""Online session workflow coordinator for KSeF."""

from __future__ import annotations

import base64
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from ksef.models.sessions import (
    EncryptionInfo,
    FormCode,
    OpenOnlineSessionRequest,
    SendInvoiceRequest,
    SendInvoiceResponse,
)

if TYPE_CHECKING:
    from ksef.client import AsyncKSeFClient
    from ksef.coordinators.auth import AuthSession
    from ksef.crypto.service import CryptographyService, SessionMaterials

_FORM_CODE_MAP: dict[str, FormCode] = {
    "FA(3)": FormCode(
        system_code="FA (3)",
        schema_version="FA_2025010901",
        value="FA",
    ),
}


class OnlineSessionContext:
    """Context manager for an open KSeF online session."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        auth_session: AuthSession,
        crypto: CryptographyService,
        session_materials: SessionMaterials,
        session_reference_number: str,
    ) -> None:
        self._client = client
        self._auth_session = auth_session
        self._crypto = crypto
        self._materials = session_materials
        self._session_ref = session_reference_number

    async def send_invoice_xml(
        self,
        xml_bytes: bytes,
        *,
        offline_mode: bool = False,
    ) -> SendInvoiceResponse:
        """Encrypt XML bytes and send to KSeF as an invoice."""

        # Compute metadata of original (plaintext) invoice
        plain_meta = self._crypto.get_metadata(xml_bytes)

        # Encrypt with the session AES key/IV
        encrypted = self._crypto.encrypt_aes256(
            xml_bytes,
            self._materials.key,
            self._materials.iv,
        )

        # Compute metadata of encrypted content
        enc_meta = self._crypto.get_metadata(encrypted)

        # Base64-encode the encrypted content for the API
        encrypted_b64 = base64.b64encode(encrypted).decode()

        request = SendInvoiceRequest(
            invoice_hash=plain_meta.hash_sha,
            invoice_size=plain_meta.file_size,
            encrypted_invoice_hash=enc_meta.hash_sha,
            encrypted_invoice_size=enc_meta.file_size,
            encrypted_invoice_content=encrypted_b64,
            offline_mode=offline_mode,
        )

        access_token = await self._auth_session.get_access_token()
        return await self._client.online.send_invoice(
            request,
            self._session_ref,
            access_token=access_token,
        )

    async def send_invoice(
        self,
        invoice_obj: object,
        *,
        offline_mode: bool = False,
    ) -> SendInvoiceResponse:
        """Serialize an xsdata model to XML then send it."""
        from ksef.xml import serialize_to_xml

        xml_bytes = serialize_to_xml(invoice_obj)
        return await self.send_invoice_xml(xml_bytes, offline_mode=offline_mode)

    async def close(self) -> None:
        """Close the online session."""
        access_token = await self._auth_session.get_access_token()
        await self._client.online.close(self._session_ref, access_token=access_token)

    async def __aenter__(self) -> OnlineSessionContext:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()


class AsyncOnlineSessionManager:
    """Manages the lifecycle of a KSeF online invoice session."""

    def __init__(
        self,
        client: AsyncKSeFClient,
        auth_session: AuthSession,
        *,
        crypto: CryptographyService | None = None,
    ) -> None:
        self._client = client
        self._auth_session = auth_session
        self._crypto = crypto

    def _get_crypto(self) -> CryptographyService:
        if self._crypto is None:
            from ksef.crypto.service import CryptographyService
            self._crypto = CryptographyService()
        return self._crypto

    @asynccontextmanager
    async def open(
        self,
        schema_version: str = "FA(3)",
        *,
        upo_version: str | None = None,
    ) -> AsyncGenerator[OnlineSessionContext, None]:
        """Open an online session and yield an OnlineSessionContext."""
        crypto = self._get_crypto()

        form_code = _FORM_CODE_MAP.get(schema_version)
        if form_code is None:
            raise ValueError(
                f"Unknown schema_version {schema_version!r}. "
                f"Supported: {list(_FORM_CODE_MAP)}"
            )

        materials = crypto.generate_session_materials()

        encryption_info = EncryptionInfo(
            encrypted_symmetric_key=base64.b64encode(materials.encrypted_key).decode(),
            initialization_vector=base64.b64encode(materials.iv).decode(),
        )

        open_request = OpenOnlineSessionRequest(
            form_code=form_code,
            encryption=encryption_info,
        )

        access_token = await self._auth_session.get_access_token()
        open_resp = await self._client.online.open(
            open_request,
            access_token=access_token,
            upo_version=upo_version,
        )

        ctx = OnlineSessionContext(
            client=self._client,
            auth_session=self._auth_session,
            crypto=crypto,
            session_materials=materials,
            session_reference_number=open_resp.reference_number,
        )

        try:
            yield ctx
        finally:
            pass  # Caller is responsible for closing via context manager or explicit close()

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
    "FA(2)": FormCode(system_code="FA (2)", schema_version="1-0E", value="FA"),
    "FA(3)": FormCode(system_code="FA (3)", schema_version="1-0E", value="FA"),
    "FA_RR": FormCode(system_code="FA_RR (1)", schema_version="1-1E", value="FA_RR"),
    "PEF(3)": FormCode(system_code="PEF (3)", schema_version="2-1", value="PEF"),
    "PEF_KOR(3)": FormCode(system_code="PEF_KOR (3)", schema_version="2-1", value="PEF"),
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
        self._closed = False

    @property
    def reference_number(self) -> str:
        """The session reference number."""
        return self._session_ref

    async def send_invoice_xml(
        self,
        xml_bytes: bytes,
        *,
        offline_mode: bool = False,
    ) -> SendInvoiceResponse:
        """Encrypt XML bytes and send to KSeF as an invoice."""
        if self._closed:
            from ksef.exceptions import KSeFSessionError

            raise KSeFSessionError("Cannot send invoice: session is already closed")
        plain_meta = self._crypto.get_metadata(xml_bytes)
        encrypted = self._crypto.encrypt_aes256(xml_bytes, self._materials.key, self._materials.iv)
        enc_meta = self._crypto.get_metadata(encrypted)
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
        """Close the online session (idempotent)."""
        if self._closed:
            return
        access_token = await self._auth_session.get_access_token()
        await self._client.online.close(self._session_ref, access_token=access_token)
        self._closed = True

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
            raise ValueError(f"Unknown schema_version {schema_version!r}. Supported: {list(_FORM_CODE_MAP)}")

        materials = crypto.generate_session_materials()

        encryption_info = EncryptionInfo.from_session_materials(materials)

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
            await ctx.close()

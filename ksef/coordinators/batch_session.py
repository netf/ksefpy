"""Batch session workflow coordinator for KSeF."""

from __future__ import annotations

import base64
import io
import zipfile
from typing import TYPE_CHECKING

from ksef.coordinators.online_session import _FORM_CODE_MAP
from ksef.models.sessions import EncryptionInfo

if TYPE_CHECKING:
    from ksef.client import AsyncKSeFClient
    from ksef.coordinators.auth import AuthSession
    from ksef.crypto.service import CryptographyService


class BatchSessionContext:
    """Collects invoices in memory and builds a ZIP archive for batch upload."""

    def __init__(self) -> None:
        self._invoices: list[bytes] = []

    def add_invoice_xml(self, xml_bytes: bytes) -> None:
        """Add raw XML bytes as an invoice to the batch."""
        self._invoices.append(xml_bytes)

    def add_invoice(self, invoice_obj: object) -> None:
        """Serialize an xsdata model to XML and add it to the batch."""
        from ksef.xml import serialize_to_xml

        self._invoices.append(serialize_to_xml(invoice_obj))

    def _build_zip(self) -> bytes:
        """Build a ZIP archive containing all added invoices."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, xml_bytes in enumerate(self._invoices):
                zf.writestr(f"invoice_{idx + 1:04d}.xml", xml_bytes)
        return buf.getvalue()

    @property
    def invoice_count(self) -> int:
        return len(self._invoices)


class AsyncBatchSessionManager:
    """Manages the lifecycle of a KSeF batch invoice session."""

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

    def new_context(self) -> BatchSessionContext:
        """Create a fresh BatchSessionContext for collecting invoices."""
        return BatchSessionContext()

    async def upload(
        self,
        context: BatchSessionContext,
        *,
        schema_version: str = "FA(3)",
    ) -> dict:
        """Build a ZIP from the context and upload it as a batch session.

        Returns the raw API response dict from the batch session endpoint.
        """
        form_code = _FORM_CODE_MAP.get(schema_version)
        if form_code is None:
            raise ValueError(
                f"Unknown schema_version {schema_version!r}. "
                f"Supported: {list(_FORM_CODE_MAP)}"
            )

        crypto = self._get_crypto()
        materials = crypto.generate_session_materials()

        zip_bytes = context._build_zip()
        encrypted_zip = crypto.encrypt_aes256(zip_bytes, materials.key, materials.iv)
        plain_meta = crypto.get_metadata(zip_bytes)
        enc_meta = crypto.get_metadata(encrypted_zip)

        encryption_info = EncryptionInfo.from_session_materials(materials)

        access_token = await self._auth_session.get_access_token()

        payload = {
            "formCode": form_code.model_dump(by_alias=True),
            "encryption": encryption_info.model_dump(by_alias=True),
            "invoiceCount": context.invoice_count,
            "invoicesHash": plain_meta.hash_sha,
            "invoicesSize": plain_meta.file_size,
            "encryptedInvoicesHash": enc_meta.hash_sha,
            "encryptedInvoicesSize": enc_meta.file_size,
            "encryptedInvoicesContent": base64.b64encode(encrypted_zip).decode(),
        }

        return await self._client.batch.open(payload, access_token=access_token)

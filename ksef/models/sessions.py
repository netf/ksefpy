from __future__ import annotations

import base64
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import Field

from ksef.models.common import KSeFModel, OperationStatusInfo

if TYPE_CHECKING:
    from ksef.crypto.service import SessionMaterials


class FormCode(KSeFModel):
    system_code: str
    schema_version: str
    value: str


class EncryptionInfo(KSeFModel):
    encrypted_symmetric_key: str
    initialization_vector: str

    @classmethod
    def from_session_materials(cls, materials: SessionMaterials) -> EncryptionInfo:
        """Build from CryptographyService session materials."""
        return cls(
            encrypted_symmetric_key=base64.b64encode(materials.encrypted_key).decode(),
            initialization_vector=base64.b64encode(materials.iv).decode(),
        )


class FileMetadata(KSeFModel):
    hash_sha: str = Field(alias="hashSHA")
    file_size: int


class OpenOnlineSessionRequest(KSeFModel):
    form_code: FormCode
    encryption: EncryptionInfo


class OpenOnlineSessionResponse(KSeFModel):
    reference_number: str
    valid_until: datetime


class SendInvoiceRequest(KSeFModel):
    invoice_hash: str
    invoice_size: int
    encrypted_invoice_hash: str
    encrypted_invoice_size: int
    encrypted_invoice_content: str
    offline_mode: bool = False
    hash_of_corrected_invoice: str | None = None


class SendInvoiceResponse(KSeFModel):
    reference_number: str


class SessionStatusResponse(KSeFModel):
    status: OperationStatusInfo | None = None
    upo: dict | None = None
    invoice_count: int | None = None
    successful_invoice_count: int | None = None
    failed_invoice_count: int | None = None
    valid_until: datetime | None = None
    date_created: datetime | None = None
    date_updated: datetime | None = None

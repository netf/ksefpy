from __future__ import annotations
from datetime import datetime
from ksef.models.common import KSeFModel, OperationStatusInfo


class InvoiceMetadataQuery(KSeFModel):
    date_from: datetime
    date_to: datetime
    nip_sender: str | None = None
    nip_recipient: str | None = None
    page: int = 0
    page_size: int = 10


class InvoiceMetadata(KSeFModel):
    ksef_number: str
    subject_nip: str | None = None
    invoice_date: datetime | None = None
    net_amount: str | None = None
    vat_amount: str | None = None
    gross_amount: str | None = None


class InvoiceMetadataResponse(KSeFModel):
    items: list[InvoiceMetadata] = []
    continuation_token: str | None = None


class ExportRequest(KSeFModel):
    date_from: datetime
    date_to: datetime
    only_metadata: bool = False


class ExportStatusResponse(KSeFModel):
    status: OperationStatusInfo
    reference_number: str | None = None

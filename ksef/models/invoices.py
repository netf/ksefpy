from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel, OperationStatusInfo


class DateRange(KSeFModel):
    date_type: str
    from_date: datetime = None
    to_date: datetime = None


class InvoiceMetadataQuery(KSeFModel):
    subject_type: str
    date_range: DateRange | None = None
    ksef_number: str | None = None
    invoice_number: str | None = None
    seller_nip: str | None = None


class InvoiceMetadata(KSeFModel):
    ksef_number: str | None = None
    invoice_number: str | None = None
    issue_date: datetime | None = None
    seller: dict | None = None
    buyer: dict | None = None
    net_amount: str | None = None
    vat_amount: str | None = None
    gross_amount: str | None = None
    currency: str | None = None
    invoice_type: str | None = None
    invoicing_mode: str | None = None


class InvoiceMetadataResponse(KSeFModel):
    invoices: list[InvoiceMetadata] = []
    has_more: bool = False
    is_truncated: bool = False


class ExportFilters(KSeFModel):
    subject_type: str | None = None
    date_range: DateRange | None = None


class ExportRequest(KSeFModel):
    filters: ExportFilters | None = None
    encryption: dict | None = None
    only_metadata: bool = False


class ExportStatusResponse(KSeFModel):
    status: OperationStatusInfo | None = None
    reference_number: str | None = None

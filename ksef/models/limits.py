from __future__ import annotations

from pydantic import Field

from ksef.models.common import KSeFModel


class SessionLimitInfo(KSeFModel):
    max_invoice_size_in_mb: int | None = Field(default=None, alias="maxInvoiceSizeInMB")
    max_invoice_with_attachment_size_in_mb: int | None = Field(default=None, alias="maxInvoiceWithAttachmentSizeInMB")
    max_invoices: int | None = None


class ContextLimits(KSeFModel):
    online_session: SessionLimitInfo | None = None
    batch_session: SessionLimitInfo | None = None


class EnrollmentLimit(KSeFModel):
    max_enrollments: int | None = None


class CertificateLimitDetail(KSeFModel):
    max_certificates: int | None = None


class SubjectLimits(KSeFModel):
    enrollment: EnrollmentLimit | None = None
    certificate: CertificateLimitDetail | None = None


class RateLimitGroup(KSeFModel):
    per_second: int | None = None
    per_minute: int | None = None
    per_hour: int | None = None


class RateLimitsResponse(KSeFModel):
    model_config = {"extra": "allow"}
    online_session: RateLimitGroup | None = None
    batch_session: RateLimitGroup | None = None
    invoice_send: RateLimitGroup | None = None

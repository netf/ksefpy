from __future__ import annotations
from datetime import datetime
from ksef.models.common import KSeFModel


class CertificateLimitResponse(KSeFModel):
    limit: int
    active_count: int
    can_enroll: bool


class CertificateEnrollmentDataResponse(KSeFModel):
    distinguished_name: dict


class CertificateEnrollRequest(KSeFModel):
    name: str
    certificate_type: str
    csr: str
    valid_from: datetime | None = None


class CertificateEnrollResponse(KSeFModel):
    reference_number: str


class CertificateEnrollmentStatusResponse(KSeFModel):
    status: str
    certificate_serial_number: str | None = None


class CertificateRetrieveRequest(KSeFModel):
    serial_numbers: list[str]


class CertificateInfo(KSeFModel):
    certificate: str
    serial_number: str | None = None
    name: str | None = None
    certificate_type: str | None = None
    status: str | None = None


class CertificateQueryRequest(KSeFModel):
    status: str | None = None
    name: str | None = None
    certificate_type: str | None = None
    page: int = 0
    page_size: int = 10


class CertificateQueryResponse(KSeFModel):
    items: list[CertificateInfo] = []
    continuation_token: str | None = None

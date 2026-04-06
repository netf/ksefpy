from __future__ import annotations

from datetime import datetime

from ksef.models.common import KSeFModel, OperationStatusInfo


class CertificateLimitInfo(KSeFModel):
    remaining: int
    limit: int


class CertificateLimitResponse(KSeFModel):
    can_request: bool
    enrollment: CertificateLimitInfo
    certificate: CertificateLimitInfo


class CertificateEnrollmentDataResponse(KSeFModel):
    common_name: str
    country_name: str
    given_name: str | None = None
    surname: str | None = None
    serial_number: str | None = None
    unique_identifier: str | None = None
    organization_name: str | None = None
    organization_identifier: str | None = None


class CertificateEnrollRequest(KSeFModel):
    certificate_name: str
    certificate_type: str
    csr: str
    valid_from: datetime | None = None


class CertificateEnrollResponse(KSeFModel):
    reference_number: str
    timestamp: datetime


class CertificateEnrollmentStatusResponse(KSeFModel):
    status: OperationStatusInfo
    certificate_serial_number: str | None = None
    request_date: datetime


class CertificateRetrieveRequest(KSeFModel):
    certificate_serial_numbers: list[str]


class CertificateInfo(KSeFModel):
    certificate_serial_number: str | None = None
    name: str | None = None
    type: str | None = None
    common_name: str | None = None
    status: OperationStatusInfo | None = None
    subject_identifier: dict | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    last_use_date: datetime | None = None
    request_date: datetime | None = None


class CertificateQueryRequest(KSeFModel):
    status: str | None = None
    name: str | None = None
    type: str | None = None
    certificate_serial_number: str | None = None
    expires_after: datetime | None = None


class CertificateQueryResponse(KSeFModel):
    certificates: list[CertificateInfo] = []
    has_more: bool = False

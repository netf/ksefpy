from __future__ import annotations
from ksef.models.common import ContextIdentifier, KSeFModel, OperationStatusInfo


class PersonPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[str]
    subject_details: dict | None = None


class EntityPermissionGrantRequest(KSeFModel):
    subject_identifier: ContextIdentifier
    permissions: list[str]
    can_delegate: bool = False
    subject_details: dict | None = None


class PermissionOperationStatusResponse(KSeFModel):
    status: OperationStatusInfo
    reference_number: str | None = None


class PermissionQueryRequest(KSeFModel):
    page: int = 0
    page_size: int = 10


class PermissionGrantResponse(KSeFModel):
    reference_number: str
